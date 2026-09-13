# Architecture

This document describes the architecture and design principles of Workload Profile Controller.

The architecture separates workload policy from infrastructure-specific implementation so that the controller can reason about desired states without depending on a particular infrastructure provider.

The current implementation uses Proxmox VE as its first backend.

---

# Architectural goals

The architecture is designed around five primary goals:

1. **Safety** — infrastructure mutations must happen only after required preconditions are satisfied.
2. **Determinism** — the same configuration and infrastructure state should produce the same transition plan.
3. **Provider independence** — the core controller should not depend on Proxmox-specific concepts.
4. **Testability** — policy and state-transition behavior should be testable without requiring real infrastructure.
5. **Extensibility** — additional infrastructure backends should be possible without redesigning the core domain model.

---

# High-level architecture

The system can be represented as:

```text id="e0by6h"
                     Configuration
                          │
                          ▼
                       Validator
                          │
                          ▼
                        Policy
                          │
                          ▼
                   Transition Plan
                          │
                          ▼
                      Controller
                          │
                          ▼
                       Backend
                          │
              ┌───────────┴───────────┐
              │                       │
           Proxmox                  Future
           Backend                 Backends
```

The most important architectural boundary is between the **core domain** and the **backend implementations**.

---

# Core domain

The core domain contains concepts that should remain independent of any infrastructure provider.

Current core modules include:

```text id="8f2p1c"
workload_profile_controller/
├── application.py
├── backend.py
├── cli.py
├── config.py
├── config_loader.py
├── config_validator.py
├── controller.py
├── errors.py
└── policy.py
```

The core does not need to know how Proxmox represents a VM, how an AWS instance is identified, or how another provider exposes lifecycle operations.

Instead, it operates on abstract resources and profiles.

---

# Configuration

Configuration defines the desired workload model.

There are two fundamental concepts:

```text id="k8q3v1"
Resource
    │
    └── abstract workload/resource identity

Profile
    │
    ├── running resources
    └── stopped resources
```

A resource is identified by its configuration key.

A profile describes the desired state of every configured resource.

For example:

```yaml id="w8r4p2"
resources:
  monitoring:
    description: "Monitoring workload"

  compute:
    description: "Compute workload"

profiles:
  profile1:
    description: "Normal operation"
    running:
      - monitoring
    stopped:
      - compute

  profile2:
    description: "Compute workload"
    running:
      - compute
    stopped:
      - monitoring
```

The configuration therefore represents a set of complete infrastructure states.

---

# Configuration validation

Configuration validation happens before the configuration is used by the controller.

The validator guarantees that profiles are structurally deterministic.

Important invariants include:

* resources must exist;
* profile references must point to known resources;
* a resource cannot be both running and stopped;
* duplicate resource references are rejected;
* every resource must have exactly one state;
* every profile must describe the same resource universe;
* profiles cannot be empty;
* profile state must be complete.

These rules are important because the transition engine assumes that a profile represents an unambiguous desired state.

---

# Policy

The policy layer determines **what should change** between two profiles.

It does not perform infrastructure operations.

Its primary responsibility is to generate a `TransitionPlan`.

Conceptually:

```text id="2p7d4z"
Source Profile
      │
      │
      ▼
    Policy
      │
      │
      ▼
Target Profile
      │
      ▼
Transition Plan
```

For example:

```text id="3q6m8s"
Source:
  monitoring = running
  compute    = stopped

Target:
  monitoring = stopped
  compute    = running
```

The policy generates:

```text id="r5c2n7"
STOP monitoring
START compute
```

The policy does not know whether `monitoring` is a QEMU VM, an LXC container, a cloud instance, or something else.

---

# TransitionPlan

A `TransitionPlan` is an immutable representation of the operations required to move from one profile to another.

Each action contains:

* an action type;
* a resource identifier.

The current action types are:

```text id="h3q8w1"
STOP
START
```

The plan is generated before infrastructure mutation begins.

This separation provides several benefits:

* transition planning can be tested independently;
* the CLI can plan a transition;
* the controller does not need to calculate policy decisions;
* future interfaces can display planned operations before execution.

---

# Controller

The controller is responsible for **safe execution** of a transition plan.

It sits between policy and infrastructure.

```text id="7z4n2m"
Policy
  │
  ▼
TransitionPlan
  │
  ▼
Controller
  │
  ▼
Backend
```

The controller enforces runtime invariants that cannot be guaranteed by static configuration alone.

---

# Controller state machine

The controller has three states:

```text id="v8p1k4"
IDLE
  │
  │ transition requested
  ▼
TRANSITIONING
  │
  ├──────── success ───────► IDLE
  │
  └──────── failure ───────► LOCKED

LOCKED
  │
  └── requires explicit recovery/reconciliation
```

### IDLE

The controller is ready to accept a transition.

### TRANSITIONING

A transition is currently being executed.

### LOCKED

A transition failed after infrastructure mutation began, or the observed infrastructure state does not correspond to any configured profile.

The locked state is intentionally conservative.

The controller does not assume that infrastructure is safe simply because an operation failed.

---

# Preconditions

Before executing a transition, the controller validates the source profile.

Every resource in the source profile must match its expected state.

For example, if the source profile specifies:

```text id="p5c8x2"
monitoring = running
compute    = stopped
```

the controller verifies both conditions before making changes.

If the current infrastructure does not match the expected source state, the transition is rejected before mutation begins.

This prevents the controller from acting on an unexpected infrastructure state.

---

# Target resource preflight

The controller also validates that all resources required by the target profile can be resolved by the backend before the first state-changing operation.

This is particularly important for provider implementations where resource resolution may fail.

For example:

```text id="n4j7v2"
Target:
  compute
  monitoring
  application

          │
          ▼

Resolve all resources

          │
          ├── success → continue
          │
          └── failure → abort before mutation
```

A missing or ambiguous resource must not result in a partially executed transition.

---

# Transition execution

Once preconditions are satisfied, the controller executes the transition plan.

The general execution model is:

```text id="u7k3m1"
Validate source
      │
      ▼
Validate target resources
      │
      ▼
Build plan
      │
      ▼
Set TRANSITIONING
      │
      ▼
Execute STOP operations
      │
      ▼
Confirm STOPPED
      │
      ▼
Execute START operations
      │
      ▼
Confirm RUNNING
      │
      ▼
Validate target profile
      │
      ▼
Set IDLE
```

If an exception occurs after the transition has started:

```text id="c5w9q2"
TRANSITIONING
      │
      ▼
   failure
      │
      ▼
   LOCKED
```

---

# Stop-before-start invariant

The controller intentionally separates stopping and starting through the transition plan.

When a resource must stop before another resource can start, the stop operation is completed and its resulting state is verified before the next operation proceeds.

The invariant is:

```text id="f2m8r6"
START target
     ▲
     │
CONFIRM stopped
     ▲
     │
STOP conflicting resource
```

This is especially important for resources that share constrained infrastructure.

The controller does not assume that an API request returning successfully means that the resource has already reached the requested state.

---

# No forced shutdown

The controller does not use forced-stop operations as part of normal transitions.

A shutdown request is followed by state verification.

If the resource does not reach the expected stopped state within the configured timeout, the transition fails.

This favors predictable failure over potentially destructive recovery behavior.

---

# Backend abstraction

The core defines a minimal backend interface:

```text id="q4t8y1"
get_status(resource_id)
start(resource_id)
stop(resource_id)
```

The controller interacts only with this interface.

The backend translates these abstract operations into provider-specific API calls.

Conceptually:

```text id="j6p2s8"
Controller
    │
    │ start("compute")
    ▼
 Backend
    │
    │ provider-specific operation
    ▼
Infrastructure
```

This prevents provider-specific implementation details from leaking into the controller.

---

# Backend status model

The backend exposes an abstract resource state model:

```text id="m8x3v5"
RUNNING
STOPPED
STARTING
STOPPING
UNKNOWN
```

The controller uses these states when validating transitions.

Provider-specific states are translated by the backend into this common representation.

---

# Proxmox backend

The Proxmox backend is located under:

```text id="b3r7k2"
src/workload_profile_controller/backends/proxmox/
```

Current components include:

```text id="x6p9m4"
proxmox/
├── auth.py
├── backend.py
├── config.py
├── config_loader.py
├── discovery.py
├── errors.py
├── factory.py
├── http_client.py
├── inventory.py
├── resource_client.py
├── task.py
└── task_waiter.py
```

Each component has a specific responsibility.

---

# Proxmox resource discovery

The Proxmox backend discovers resources from the configured node.

The current implementation queries both:

```text id="r8m2v5"
/nodes/{node}/qemu
/nodes/{node}/lxc
```

The resulting infrastructure resources are converted into an internal inventory representation.

The controller never needs to know whether a resource originated from the QEMU or LXC API.

---

# Proxmox inventory

The backend represents discovered resources internally as:

```text id="k2v7n9"
ProxmoxResource
├── resource_type
├── proxmox_id
└── name
```

The inventory is responsible for resolving abstract resource names.

The resolution algorithm is intentionally strict.

```text id="s5x1m8"
Configured resource name
          │
          ▼
Exact name matching
          │
     ┌────┼────┐
     │    │    │
     ▼    ▼    ▼
    0     1    >1
matches match matches
     │    │    │
     ▼    ▼    ▼
  error  valid error
```

No arbitrary resource is selected when a name is ambiguous.

---

# Why exact matching?

Infrastructure automation should avoid guessing.

Consider:

```text id="y4q7c1"
QEMU:
  name = application

LXC:
  name = application
```

Selecting one of these resources automatically could result in an unexpected infrastructure mutation.

The backend therefore raises an ambiguity error.

The configuration or infrastructure must be corrected before the transition can proceed.

---

# Proxmox-specific implementation boundary

The following concepts belong exclusively to the Proxmox backend:

* QEMU;
* LXC;
* Proxmox IDs;
* Proxmox API endpoints;
* UPIDs;
* Proxmox API tokens;
* Proxmox task states;
* Proxmox-specific HTTP errors.

The core controller does not depend on them.

This boundary is important for future backend implementations.

---

# HTTP client

The Proxmox HTTP client is responsible for communication with the Proxmox API.

Its responsibilities include:

* HTTPS connections;
* TLS configuration;
* request construction;
* authentication headers;
* HTTP response handling;
* error translation.

TLS configuration supports:

* certificate verification;
* custom CA files;
* a TLS server name separate from the network connection host.

The HTTP client does not contain workload policy.

---

# Authentication

The Proxmox backend uses API-token authentication.

Authentication details remain inside the Proxmox backend.

The core controller never receives or manipulates provider credentials.

This separation reduces the scope of sensitive configuration.

---

# Asynchronous tasks

Many Proxmox operations are asynchronous.

The backend therefore separates:

```text id="v3m7q1"
Request operation
      │
      ▼
Receive task identifier
      │
      ▼
Wait for task
      │
      ▼
Validate task result
```

Task monitoring is implemented by the Proxmox backend.

The controller receives the final operation result through the backend abstraction.

---

# Reconciliation

Reconciliation is deliberately observational.

The controller compares the actual infrastructure state with the configured profiles.

Conceptually:

```text id="p8x2m6"
Infrastructure state
        │
        ▼
Compare with profiles
        │
   ┌────┴────┐
   │         │
 exact      no match
 match        │
   │          ▼
   ▼        LOCKED
 profile
```

If the infrastructure exactly matches a configured profile, reconciliation identifies that profile.

If it matches no profile, the controller enters the locked state.

Reconciliation does not automatically start or stop resources.

This prevents unexpected infrastructure mutations during recovery.

---

# Transition planning

Transition planning uses the same policy layer used for real transitions.

The planning flow is:

```text
Current infrastructure state
              │
              ▼
       Current profile
              │
              ▼
           Policy
              │
              ▼
      TransitionPlan
              │
              ▼
           Display

---

# Application layer

The application layer acts as the composition root.

Its responsibility is to assemble:

```text id="q7m3x9"
Configuration
      │
      ├── Config loader
      │
      └── Backend configuration
                    │
                    ▼
                  Backend
                    │
                    ▼
                Controller
```

The application layer is therefore where concrete backend implementations are selected.

The core domain itself remains provider-independent.

---

# CLI

The CLI provides an interface to the application layer.

Current commands include:

```text id="m2r8k4"
profiles
status
plan
transition
```

The CLI should remain thin.

It is responsible for:

* parsing arguments;
* loading configuration;
* invoking application/controller operations;
* presenting results and errors.

Business rules should remain outside the CLI.

---

# Error handling

Errors are separated according to responsibility.

Core errors represent provider-independent conditions.

Examples include:

```text id="h9v4p2"
BackendError
ResourceNotFoundError
ResourceAmbiguousError
BackendUnavailableError
InvalidResourceStateError
TaskTimeoutError
TaskFailedError
```

The Proxmox backend also has provider-specific errors such as HTTP failures.

Provider-specific errors should remain within the backend boundary unless they need to be translated into a generic core error.

---

# Testing architecture

The architecture is designed so that most behavior can be tested without a real Proxmox environment.

Tests can operate at different levels:

```text id="x7p2m9"
Core
 │
 ├── configuration
 ├── validation
 ├── policy
 ├── controller
 └── CLI
       │
       ▼
Backend
 │
 ├── Proxmox configuration
 ├── authentication
 ├── HTTP client
 ├── inventory
 ├── discovery
 ├── resource operations
 └── task handling
```

This separation allows deterministic unit tests for the state machine while provider-specific behavior can be tested independently.

---

# Safety invariants

The following invariants are fundamental to the architecture.

## Invariant 1 — Validate before mutation

Required preconditions must be satisfied before infrastructure state is changed.

## Invariant 2 — Never assume asynchronous completion

A requested state change must be confirmed through backend state observation.

## Invariant 3 — Stop before conflicting start

Resources that must stop are confirmed stopped before dependent target resources are started.

## Invariant 4 — No forced stop

The controller does not use destructive forced shutdown as a normal recovery mechanism.

## Invariant 5 — Fail closed

A failed transition enters the locked state rather than claiming success.

## Invariant 6 — Reconciliation does not mutate

Reconciliation observes and classifies state but does not automatically modify infrastructure.

## Invariant 7 — Ambiguity is an error

The backend must never arbitrarily choose between multiple infrastructure resources.

---

# Extensibility

The architecture is intentionally prepared for additional backends.

A future backend could implement the same abstract interface:

```text id="c4m8x1"
Backend
  │
  ├── ProxmoxBackend
  ├── AWSBackend
  ├── GCPBackend
  └── OtherBackend
```

The core profile model would remain unchanged.

For example, a profile could continue to use:

```text id="z5r7p3"
compute
monitoring
application
```

while the backend determines what those resources represent in a particular infrastructure environment.

---

# Current limitations

The current architecture has some intentional limitations.

### Single configured Proxmox node

The current Proxmox backend operates against one explicitly configured node.

### Resource-name resolution

The Proxmox backend currently relies on exact resource names rather than provider IDs.

### No automatic recovery

A failed transition does not automatically attempt to reverse already completed operations.

The controller locks instead.

### No persistent controller state

The current controller state is maintained in memory.

Persistent operational state and recovery workflows may be added in future versions.

### No WebUI

The current interface is CLI-based.

A future WebUI can consume the same application/controller layer without duplicating the transition logic.

---

# Future architecture

As additional backends and interfaces are introduced, the intended architecture is:

```text
                         User Interfaces
                    ┌──────────┴──────────┐
                    │                     │
                   CLI                  WebUI
                    │                     │
                    └──────────┬──────────┘
                               │
                        Application Layer
                               │
                         Core Controller
                               │
                        Transition Policy
                               │
                         Backend Interface
                               │
              ┌────────────────┼────────────────┐
              │                │                │
           Proxmox            AWS              GCP
           Backend          Backend          Backend
```

The important principle is that additional interfaces should reuse the same controller and policy layers rather than implementing their own transition logic.

---

# Architectural principle

The central architectural principle of Workload Profile Controller is:

> **Describe desired infrastructure states declaratively, calculate transitions deterministically, and allow infrastructure-specific backends to execute them safely.**

The controller is therefore not intended to be a generic infrastructure provisioning system.

Its responsibility is narrower:

**safely move infrastructure between explicitly defined operational states.**
