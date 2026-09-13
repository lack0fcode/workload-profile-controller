# Workload Profile Controller

[![CI](https://github.com/lack0fcode/workload-profile-controller/actions/workflows/ci.yml/badge.svg)](https://github.com/lack0fcode/workload-profile-controller/actions/workflows/ci.yml)

A safe and configurable workload profile controller for orchestrating mutually exclusive resource states across infrastructure backends.

The project was designed around a simple problem: different workloads may compete for the same infrastructure resources, making manual switching between operational configurations error-prone.

Instead of manually starting and stopping resources, the controller defines **profiles** describing the desired state of the infrastructure and performs deterministic, validated transitions between them.

The first supported infrastructure backend is **Proxmox VE**.

---

## Overview

A workload profile describes which resources must be running and which must be stopped.

For example:

```yaml
profiles:
  profile1:
    description: "Normal operation"
    running:
      - monitoring
      - application
    stopped:
      - compute

  profile2:
    description: "Compute workload"
    running:
      - compute
    stopped:
      - monitoring
      - application
```

The controller can then transition between these profiles:

```text
                 Workload Profile Controller

                         Profile
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
                     Backend API
                            │
                            ▼
                       Proxmox
```

The core logic is intentionally independent of Proxmox. Proxmox is implemented as a backend, allowing other infrastructure providers to be added in the future.

---

## Why?

Manually switching infrastructure between different workload configurations can introduce dangerous situations.

For example:

* starting a resource before another resource has stopped;
* assuming that a shutdown completed when it did not;
* starting a workload while another conflicting workload is still running;
* recovering automatically from an unexpected partial transition;
* losing track of the actual infrastructure state.

The controller therefore treats profile transitions as **stateful and deterministic operations**.

A transition only proceeds when its preconditions are satisfied.

If a transition fails after infrastructure changes have started, the controller enters a locked state rather than pretending that the desired profile was reached.

---

## Core principles

The controller is designed around several safety invariants.

### Validate before mutating

The controller validates the current state and resolves the target resources before performing the first state-changing operation.

### Stop before start

When resources conflict between profiles, resources from the previous profile are stopped and confirmed stopped before new resources are started.

### Confirm every operation

After requesting a resource transition, the controller verifies its resulting state.

### Never force-stop

The controller does not use destructive forced shutdown operations.

### Fail closed

If a transition cannot be completed reliably, the controller enters a locked state instead of assuming success.

### Reconcile is observational

Reconciliation observes the infrastructure and determines which configured profile matches the current state.

It does not automatically start or stop resources.

### Exact resource resolution

Backends must resolve configured resource identifiers deterministically.

For the Proxmox backend, resource names are matched exactly. Ambiguous names are rejected rather than resolved arbitrarily.

---

## Profiles

Profiles are completely configurable.

A profile contains:

* a name;
* an optional description;
* resources that must be running;
* resources that must be stopped.

Every configured resource must have exactly one state in every profile.

For example:

```yaml
resources:
  monitoring:
    description: "Monitoring workload"

  compute:
    description: "Compute workload"

  application:
    description: "Application workload"
```

Profiles then describe the desired state of those resources.

This separation between **resource identity** and **infrastructure-specific identifiers** allows the same profile model to remain independent of the underlying provider.

---

## Supported backend

### Proxmox VE

The current backend supports:

* QEMU virtual machines;
* LXC containers;
* Proxmox API authentication using API tokens;
* TLS certificate verification;
* configurable TLS server names;
* resource discovery;
* exact resource-name resolution;
* start and stop operations;
* asynchronous task monitoring;
* shutdown timeouts.

The core controller does not need to know whether a resource is a QEMU VM or an LXC container.

That information remains inside the Proxmox backend.

---

## Installation

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/lack0fcode/workload-profile-controller.git
cd workload-profile-controller

python -m venv .venv
```

Activate the virtual environment and install the project with its development dependencies:

```bash
python -m pip install -e ".[dev]"
```

The CLI is then available as:

```bash
wpc
```

Check the installation:

```bash
wpc --help
```

---

## Configuration

The controller uses a YAML configuration file to define resources and profiles.

An example configuration is available at:

```text
config/examples/config.example.yaml
```

Backend-specific connection settings are kept separately from the profile configuration.

For the Proxmox backend, credentials and connection parameters are provided through environment variables.

Secrets should never be committed to the repository.

See:

* [CONFIGURATION.md](config/CONFIGURATION.md)
* [SECURITY.md](SECURITY.md)

for details.

---

## CLI

The current CLI provides four main operations.

### List profiles

```bash
wpc --config config.yaml profiles
```

Lists the profiles defined in the configuration.

### Show status

```bash
wpc --config config.yaml status
```

Shows the current state of configured resources.

### Plan a transition

```bash
wpc --config config.yaml plan profile2
```

Builds and displays the transition plan without changing infrastructure.

### Perform a transition

```bash
wpc --config config.yaml transition profile2
```

Executes the transition to the selected profile.

---

## Safety model

A simplified transition looks like this:

```text
Current Profile
      │
      ▼
Validate current state
      │
      ▼
Resolve target resources
      │
      ▼
Build transition plan
      │
      ▼
Stop conflicting resources
      │
      ▼
Confirm stopped
      │
      ▼
Start target resources
      │
      ▼
Confirm running
      │
      ▼
Validate complete target profile
      │
      ▼
Transition complete
```

If an operation fails after the transition has started:

```text
Transition
    │
    ├── success ───────► target profile
    │
    └── failure ───────► LOCKED
```

The locked state prevents subsequent transitions from proceeding until the situation has been explicitly investigated.

---

## Architecture

The project separates infrastructure-independent policy from backend-specific operations.

```text
Configuration
      │
      ▼
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
      │
      ├──────── Proxmox
      │
      ├──────── AWS       (future)
      │
      └──────── GCP       (future)
```

The main components are:

### Configuration

Loads and validates resources and profiles.

### Policy

Determines what must change between two profiles and generates a deterministic transition plan.

### Controller

Enforces the safety rules and executes the transition through the backend interface.

### Backend

Provides an infrastructure-independent interface for querying, starting and stopping resources.

### Proxmox backend

Implements the backend interface using the Proxmox API and handles provider-specific resource discovery, resolution and asynchronous tasks.

More details are available in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Development

Install the development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

Run Ruff:

```bash
ruff check src tests
```

The project is developed with a strong emphasis on deterministic behavior and testable state transitions.

---

## Project status

The project is currently in active development.

The Proxmox backend and core profile transition logic are functional and covered by automated tests.

Current priorities include:

* strengthening configuration and safety validation;
* improving the CLI;
* expanding integration testing;
* adding additional backend implementations;
* developing a WebUI for profile management and operational visibility;
* establishing the packaging and release workflow.

---

## Roadmap

### Core

* [x] Configurable resources
* [x] Configurable profiles
* [x] Profile validation
* [x] Deterministic transition plans
* [x] Backend abstraction
* [x] Proxmox backend
* [x] QEMU support
* [x] LXC support
* [x] Resource discovery
* [x] Exact resource resolution
* [x] Asynchronous task monitoring
* [x] Transition locking
* [x] Reconciliation

### CLI

* [x] Profile listing
* [x] Resource status
* [x] Transition plan
* [x] Profile transitions

### Documentation

* [x] Configuration guide
* [x] Architecture documentation
* [x] Security documentation
* [x] Contribution guide

### Future

* [ ] WebUI
* [ ] Additional infrastructure backends
* [ ] Integration test environment
* [ ] Improved transition diagnostics

---

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for the full license text.

---

## Contributing

Contributions, bug reports and architectural discussions are welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
