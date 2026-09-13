# Contributing

Thank you for considering contributing to Workload Profile Controller.

This project is designed around infrastructure safety, deterministic behavior and clear separation between the core controller and infrastructure-specific backends.

Contributions should preserve these principles.

---

# Development environment

The project requires:

* Python 3.11 or newer;
* Git;
* a virtual environment;
* the project development dependencies.

Clone the repository:

```bash
git clone https://github.com/<your-account>/workload-profile-controller.git
cd workload-profile-controller
```

Create a virtual environment:

```bash
python -m venv .venv
```

Install the project with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Verify the installation:

```bash
wpc --help
```

---

# Project structure

The main source tree is organized into a provider-independent core and backend implementations.

```text
src/
└── workload_profile_controller/
    ├── application.py
    ├── backend.py
    ├── cli.py
    ├── config.py
    ├── config_loader.py
    ├── config_validator.py
    ├── controller.py
    ├── errors.py
    ├── policy.py
    └── backends/
        └── proxmox/
```

The core should remain independent of infrastructure providers.

Provider-specific code belongs inside its corresponding backend.

For example:

```text
backends/
└── proxmox/
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

---

# Core development principles

Contributions should follow these principles.

## Keep the core provider-independent

Avoid importing Proxmox-specific modules into core modules.

For example, core policy code should not depend on:

```text
QEMU
LXC
VMID
UPID
Proxmox API
```

Provider-specific concepts belong inside the backend implementation.

---

## Keep business logic out of the CLI

The CLI should primarily:

* parse arguments;
* load configuration;
* invoke application/controller operations;
* display results.

Transition rules belong in the controller and policy layers.

---

## Keep policy separate from execution

The policy layer decides **what should happen**.

The controller decides **how to safely execute it**.

The backend decides **how to communicate with the infrastructure provider**.

The separation should remain:

```text
Policy
  │
  │ desired operations
  ▼
Controller
  │
  │ safe execution
  ▼
Backend
  │
  │ provider-specific API
  ▼
Infrastructure
```

---

# Safety invariants

Changes affecting transition behavior must preserve the project's safety invariants.

In particular:

### Validate before mutation

Do not perform infrastructure mutations before required preconditions are validated.

### Stop before conflicting start

Resources that must be stopped must be confirmed stopped before conflicting resources are started.

### Confirm state changes

Do not assume that a successful API request means that the resource has reached the requested state.

### Never force-stop

Normal transition logic must not introduce destructive forced shutdown behavior.

### Fail closed

A failed transition must not be reported as successful.

### Reconciliation must remain observational

Reconciliation should not silently start or stop infrastructure.

### Ambiguity must fail

A backend must never arbitrarily choose between multiple resources matching an abstract identifier.

---

# Adding a new backend

Additional infrastructure providers should implement the core `Backend` interface.

The backend is responsible for translating abstract operations into provider-specific operations.

For example:

```text
Backend
  │
  ├── ProxmoxBackend
  ├── AWSBackend
  ├── GCPBackend
  └── Future backend
```

A new backend should provide at least:

```text
get_status(resource_id)
start(resource_id)
stop(resource_id)
```

Provider-specific concerns should remain inside the backend.

These may include:

* authentication;
* TLS;
* resource discovery;
* resource resolution;
* provider-specific state mapping;
* asynchronous task handling;
* provider-specific errors.

---

# Resource resolution

Backend implementations must resolve abstract resource identifiers deterministically.

Do not use:

* fuzzy matching;
* substring matching;
* arbitrary fallback;
* implicit provider IDs;
* "first match wins" behavior.

If zero resources match:

```text
ResourceNotFoundError
```

If multiple resources match:

```text
ResourceAmbiguousError
```

A backend must never silently select an arbitrary resource.

---

# Configuration changes

Changes to the configuration model should include corresponding validation and tests.

When adding a new configuration field, consider:

1. Is the field provider-independent?
2. Should it belong to the core configuration or a backend configuration?
3. What are its validation rules?
4. What happens when it is missing?
5. Can it create an ambiguous or unsafe state?
6. Does documentation need to be updated?

Configuration examples should remain sanitized.

Never add real credentials or private infrastructure information.

---

# Testing

Tests are required for behavioral changes.

Run the complete test suite with:

```bash
pytest
```

The project should maintain tests for:

* configuration;
* validation;
* policy;
* transition planning;
* controller behavior;
* backend behavior;
* resource resolution;
* error handling;
* CLI behavior.

---

# Testing safety behavior

Safety-related changes should include explicit tests for failure conditions.

For example:

* source profile does not match actual state;
* target resource cannot be resolved;
* target resource is ambiguous;
* stop operation fails;
* start operation fails;
* asynchronous task times out;
* target profile is not reached;
* controller enters `LOCKED`;
* reconciliation finds no matching profile.

A successful transition alone is not sufficient coverage for safety-critical logic.

---

# Unit tests

Most core behavior should be testable without real infrastructure.

Backend-independent tests should use test doubles or mocks rather than requiring a live provider.

This makes tests:

* deterministic;
* fast;
* reproducible;
* suitable for continuous integration.

---

# Integration tests

Integration tests may interact with real infrastructure when appropriate.

Integration tests should be clearly separated from unit tests and should not require developers to expose credentials in source code.

A future integration test environment should use dedicated infrastructure and credentials with limited privileges.

---

# Running Ruff

Run Ruff against the source and test code:

```bash
ruff check src tests
```

Ruff is used primarily for code quality and consistency.

A contribution does not need to blindly change behavior merely to satisfy a stylistic preference.

However, new warnings should be avoided where practical.

---

# Formatting and imports

Keep imports organized and remove imports that are no longer needed.

Follow the existing formatting conventions of the project.

Avoid introducing unrelated formatting changes into a feature or bug-fix pull request.

Small, focused diffs are easier to review.

---

# CLI changes

When adding or modifying CLI commands:

* keep command behavior explicit;
* provide useful help text;
* avoid exposing secrets;
* test argument parsing;
* test success and failure paths;
* preserve the separation between CLI and controller logic.

New commands should be documented in `README.md` and, when appropriate, in the relevant documentation.

---

# Documentation changes

Documentation is considered part of the project.

Changes to behavior should normally update the relevant documentation.

The main documentation set is:

```text
README.md
CONFIGURATION.md
ARCHITECTURE.md
SECURITY.md
CONTRIBUTING.md
```

Examples should use sanitized values.

Do not document real infrastructure credentials, private hostnames or internal addresses.

---

# Commit guidelines

Keep commits focused.

A commit should preferably represent one logical change.

Good examples:

```text
Add deterministic Proxmox resource resolution
```

```text
Add configuration validation for profile completeness
```

```text
Add transition plan command
```

Avoid combining unrelated changes such as:

```text
Fix Proxmox discovery, rewrite README, rename modules, change CLI output and update dependencies
```

unless the changes are genuinely part of the same architectural change.

---

# Pull requests

A pull request should explain:

* what changed;
* why it changed;
* how it was tested;
* whether configuration or documentation changed;
* whether the change affects infrastructure safety.

For safety-sensitive changes, describe the relevant invariants explicitly.

For example:

```text
This change preserves the stop-before-start invariant and adds
coverage for failed shutdown operations.
```

---

# Before opening a pull request

Run:

```bash
pytest
```

Then:

```bash
ruff check src tests
```

Review the Git diff:

```bash
git diff
```

Check the repository status:

```bash
git status
```

Make sure no sensitive files are staged.

In particular, verify that:

```text
.env
private keys
credentials
local infrastructure configuration
```

are not included.

---

# Security-sensitive contributions

Changes involving any of the following deserve additional review:

* authentication;
* authorization;
* credentials;
* TLS;
* resource resolution;
* infrastructure mutations;
* transition locking;
* recovery behavior;
* WebUI authentication;
* network exposure.

Do not disclose security-sensitive information in public issues or pull requests.

See [SECURITY.md](SECURITY.md) for the project's security model.

---

# Backward compatibility

When changing public behavior, consider compatibility with:

* existing configuration files;
* existing CLI commands;
* existing profiles;
* existing backend implementations;
* existing integrations.

If a breaking change is necessary, document it clearly.

---

# Adding dependencies

New dependencies should have a clear justification.

Before adding a dependency, consider:

* whether the functionality can reasonably be implemented using the standard library;
* dependency maintenance status;
* licensing;
* security history;
* package size;
* whether it belongs in runtime or development dependencies.

Avoid adding dependencies for functionality that can be implemented simply without them.

---

# Development workflow

A typical contribution workflow is:

```text
Create branch
     │
     ▼
Make focused change
     │
     ▼
Add/update tests
     │
     ▼
Update documentation
     │
     ▼
Run pytest
     │
     ▼
Run Ruff
     │
     ▼
Review diff
     │
     ▼
Commit
     │
     ▼
Open pull request
```

---

# Design discussions

Architectural changes should be discussed before implementation when they significantly affect:

* the core domain model;
* backend abstraction;
* controller state machine;
* safety invariants;
* configuration semantics;
* public CLI behavior.

The goal is to keep the architecture intentional rather than accumulating provider-specific exceptions in the core.

---

# Contribution philosophy

The project values:

* correctness over convenience;
* explicit behavior over implicit behavior;
* deterministic automation over heuristics;
* small and reviewable changes;
* strong tests around failure conditions;
* clear separation of responsibilities;
* safe failure over optimistic recovery.

The most important question when modifying the controller is:

> **What happens if this operation fails halfway through?**

A contribution should make that answer clearer, not less predictable.
