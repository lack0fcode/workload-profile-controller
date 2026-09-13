# Configuration

This document describes how to configure resources, workload profiles and backend connection settings for Workload Profile Controller.

The configuration is divided into two concerns:

1. **Workload configuration** — resources and profiles.
2. **Backend configuration** — infrastructure-specific connection settings.

This separation keeps workload definitions independent from the infrastructure provider.

---

## Configuration file

The workload configuration is defined in YAML.

A complete example is available at:

```text
config/examples/config.example.yaml
```

A basic configuration looks like this:

```yaml
resources:
  monitoring:
    description: "Monitoring workload"

  compute:
    description: "Compute workload"

  application:
    description: "Application workload"

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

---

# Resources

The `resources` section defines the abstract resources managed by the controller.

```yaml
resources:
  monitoring:
    description: "Monitoring workload"

  compute:
    description: "Compute workload"
```

Each resource consists of:

* a unique resource identifier;
* an optional description.

The resource identifier is the YAML mapping key.

For example:

```yaml
resources:
  compute:
    description: "Compute workload"
```

The resource identifier is:

```text
compute
```

The description is informational and does not participate in resource resolution.

---

## Resource identity

Resource identifiers are intentionally independent of infrastructure-specific identifiers.

The controller does not require the configuration to contain:

* Proxmox VMIDs;
* QEMU identifiers;
* LXC identifiers;
* cloud instance IDs;
* provider-specific resource IDs.

The backend is responsible for resolving the abstract resource identifier against the infrastructure.

For example:

```text
Profile configuration
        │
        ▼
     compute
        │
        ▼
     Backend
        │
        ▼
Infrastructure resource
```

This allows the same profile model to be used with different backend implementations.

---

# Profiles

The `profiles` section defines the desired operational states of the infrastructure.

Each profile contains:

* a profile identifier;
* an optional description;
* resources that must be running;
* resources that must be stopped.

Example:

```yaml
profiles:
  profile1:
    description: "Normal operation"
    running:
      - monitoring
      - application
    stopped:
      - compute
```

---

## Profile identity

The profile identifier is the YAML mapping key.

For example:

```yaml
profiles:
  profile1:
```

The profile name is:

```text
profile1
```

Profile names are used by the CLI:

```bash
wpc --config config.yaml plan profile1
```

and:

```bash
wpc --config config.yaml transition profile1
```

---

# Running resources

The `running` list contains resources that must be running when the profile is active.

Example:

```yaml
running:
  - monitoring
  - application
```

The controller considers the profile active only when all resources listed under `running` are confirmed to be running.

---

# Stopped resources

The `stopped` list contains resources that must be stopped when the profile is active.

Example:

```yaml
stopped:
  - compute
```

The controller considers the profile active only when all resources listed under `stopped` are confirmed to be stopped.

---

# Deterministic profiles

Every managed resource must have exactly one state in every profile.

A resource cannot be both running and stopped:

```yaml
profile1:
  running:
    - compute
  stopped:
    - compute
```

This configuration is invalid.

A resource also cannot be omitted from a profile:

```yaml
resources:
  monitoring:
  compute:
```

```yaml
profile1:
  running:
    - monitoring
  stopped: []
```

This configuration is invalid because `compute` has no defined state.

The purpose of this rule is to ensure that every profile represents a complete and deterministic infrastructure state.

---

# Profile consistency

All profiles must describe the same resource universe.

For example, this is valid:

```yaml
resources:
  monitoring:
  compute:
  application:

profiles:
  profile1:
    running:
      - monitoring
      - application
    stopped:
      - compute

  profile2:
    running:
      - compute
    stopped:
      - monitoring
      - application
```

Both profiles define a state for all three resources.

Adding a resource to only one profile is invalid.

---

# Transition planning

The controller compares the currently active profile with the requested target profile.

For example:

```text
profile1

running:
  monitoring
  application

stopped:
  compute
```

to:

```text
profile2

running:
  compute

stopped:
  monitoring
  application
```

produces the following conceptual transition:

```text
STOP
  monitoring
  application

START
  compute
```

The policy layer generates this transition plan before the controller performs infrastructure mutations.

The backend is responsible only for executing the resulting resource operations.

---

# Backend configuration

Backend connection settings are separate from workload profiles.

This prevents infrastructure credentials and provider-specific settings from being embedded in the YAML profile configuration.

For the Proxmox backend, connection settings are provided through environment variables.

A local `.env` file can be used during development.

Example:

```text
PVE_PROXMOX_HOST=proxmox.example.internal
PVE_PROXMOX_NODE=pve-node-01
PVE_PROXMOX_USER=controller-user@pve
PVE_PROXMOX_TOKEN_NAME=controller
PVE_PROXMOX_TOKEN_SECRET=<secret>
PVE_PROXMOX_VERIFY_TLS=true
PVE_PROXMOX_TIMEOUT=5.0
PVE_PROXMOX_TASK_TIMEOUT=120.0
PVE_PROXMOX_SHUTDOWN_TIMEOUT=120.0
PVE_PROXMOX_CA_FILE=./config/pve-root-ca.pem
PVE_PROXMOX_TLS_SERVER_NAME=pve-node-01.example.internal
```

Do not commit `.env` to Git.

The repository already excludes `.env` through `.gitignore`.

---

# Proxmox backend settings

## `PVE_PROXMOX_HOST`

The network address used to connect to the Proxmox API.

Example:

```text
PVE_PROXMOX_HOST=proxmox.example.internal
```

This value is used for the network connection.

It does not necessarily need to match the TLS server name.

This distinction is useful when the Proxmox API is accessed through an IP address while its certificate contains a DNS hostname.

---

## `PVE_PROXMOX_NODE`

The Proxmox node whose resources are managed.

Example:

```text
PVE_PROXMOX_NODE=pve-node-01
```

The current backend operates against one explicitly configured node.

---

## `PVE_PROXMOX_USER`

The Proxmox API token owner.

Example:

```text
PVE_PROXMOX_USER=controller-user
```

This value must correspond to the Proxmox authentication configuration.

---

## `PVE_PROXMOX_TOKEN_NAME`

The API token name.

Example:

```text
PVE_PROXMOX_TOKEN_NAME=controller@pve!controller
```

The token itself should be created specifically for the controller and granted only the permissions required by the deployment.

---

## `PVE_PROXMOX_TOKEN_SECRET`

The API token secret.

Example:

```text
PVE_PROXMOX_TOKEN_SECRET=<secret>
```

This is a credential and must never be committed to the repository.

Do not place real credentials in:

* YAML configuration files;
* source code;
* tests;
* documentation;
* Git commits;
* issue reports.

See [SECURITY.md](SECURITY.md) for the security model.

---

## `PVE_PROXMOX_VERIFY_TLS`

Controls TLS certificate verification.

Recommended value:

```text
PVE_PROXMOX_VERIFY_TLS=true
```

TLS verification should remain enabled in normal deployments.

Disabling certificate verification should only be considered for controlled testing environments.

---

## `PVE_PROXMOX_CA_FILE`

Optional path to a CA certificate used to validate the Proxmox API certificate.

Example:

```text
PVE_PROXMOX_CA_FILE=./config/pve-root-ca.pem
```

This is useful when the Proxmox environment uses a private or cluster-specific certificate authority.

CA files containing private infrastructure information should not be committed unless they are intentionally safe for publication.

---

## `PVE_PROXMOX_TLS_SERVER_NAME`

Optional TLS server name used during certificate validation.

Example:

```text
PVE_PROXMOX_TLS_SERVER_NAME=pve-node-01.example.internal
```

This can be different from `PVE_PROXMOX_HOST`.

For example:

```text
PVE_PROXMOX_HOST=192.0.2.10
PVE_PROXMOX_TLS_SERVER_NAME=pve-node-01.example.internal
```

The connection is made to the first value while TLS validation uses the second value.

---

## `PVE_PROXMOX_TIMEOUT`

HTTP connection/request timeout.

Example:

```text
PVE_PROXMOX_TIMEOUT=5.0
```

The default is:

```text
5.0 seconds
```

---

## `PVE_PROXMOX_TASK_TIMEOUT`

Maximum time allowed for a Proxmox API task to complete.

Example:

```text
PVE_PROXMOX_TASK_TIMEOUT=120.0
```

The default is:

```text
120 seconds
```

This applies to asynchronous Proxmox operations monitored by the backend.

---

## `PVE_PROXMOX_SHUTDOWN_TIMEOUT`

Maximum time allowed for a graceful shutdown operation.

Example:

```text
PVE_PROXMOX_SHUTDOWN_TIMEOUT=120.0
```

The controller does not use forced shutdown operations when this timeout expires.

A timeout is treated as an operation failure.

---

# Resource resolution in Proxmox

The Proxmox backend resolves configured resource identifiers using the resource `name` reported by Proxmox.

Matching is exact.

For example, if the configuration contains:

```yaml
resources:
  compute:
```

the backend searches for a Proxmox resource whose name is exactly:

```text
compute
```

The backend does not perform:

* substring matching;
* fuzzy matching;
* case-insensitive matching;
* regular-expression matching;
* whitespace normalization;
* arbitrary fallback matching.

---

## Missing resources

If no Proxmox resource matches the configured name, the backend reports a resource-not-found error.

The controller does not guess which resource was intended.

---

## Ambiguous resources

If more than one Proxmox resource has the same name, the backend reports an ambiguity error.

For example:

```text
QEMU VM:
  name = compute

LXC container:
  name = compute
```

The controller will not arbitrarily select one of them.

The configuration or infrastructure must be corrected so that the resource can be uniquely identified.

---

# QEMU and LXC

The Proxmox backend supports both:

* QEMU virtual machines;
* LXC containers.

The distinction is handled internally by the backend.

The core controller works with the abstract resource identifier:

```text
compute
```

rather than infrastructure-specific concepts such as:

```text
VMID
container ID
QEMU
LXC
```

This keeps the controller independent from Proxmox implementation details.

---

# Configuration validation

Configuration is validated before it is used by the controller.

The validator checks, among other things:

* at least one resource exists;
* resource identifiers are valid;
* profile names are consistent;
* all referenced resources exist;
* no resource appears in both `running` and `stopped`;
* no duplicate resource references exist;
* every managed resource has exactly one state;
* every profile describes the same resource universe;
* profiles represent complete deterministic states;
* empty profiles are rejected.

Invalid configuration prevents the controller from operating.

---

# Recommended workflow

A recommended configuration workflow is:

```text
Create resources
      │
      ▼
Create profiles
      │
      ▼
Validate configuration
      │
      ▼
Run plan
      │
      ▼
Inspect transition plan
      │
      ▼
Perform transition
```

Before changing infrastructure, use:

```bash
wpc --config config.yaml plan profile2
```

This allows the generated transition plan to be inspected without changing resource states.

---

# Example complete configuration

```yaml
resources:
  monitoring:
    description: "Monitoring workload"

  compute:
    description: "Compute workload"

  application:
    description: "Application workload"

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

  profile3:
    description: "Maintenance"
    running:
      - monitoring
    stopped:
      - compute
      - application
```

This configuration defines three complete operational states over the same three resources.

Each profile is deterministic and mutually exclusive.

---

# Best practices

### Keep resource names stable

Resource identifiers are part of the workload configuration. Avoid changing them unnecessarily.

### Keep infrastructure details out of profiles

Profiles should describe workloads rather than provider-specific implementation details.

### Keep credentials outside Git

Use environment variables or an appropriate secret-management mechanism.

### Keep TLS verification enabled

Use a trusted CA rather than disabling certificate verification.

### plan before transitioning

Inspect the transition plan before performing infrastructure changes.

### Use dedicated backend credentials

Create credentials specifically for the controller and grant only the permissions required for its operation.

### Treat configuration as code

Version-control safe configuration examples and review configuration changes like source-code changes.

---

## Related documentation

* [README.md](README.md) — project overview and quick start
* [ARCHITECTURE.md](ARCHITECTURE.md) — internal architecture and design
* [SECURITY.md](SECURITY.md) — security model and operational recommendations
* [CONTRIBUTING.md](CONTRIBUTING.md) — development and contribution guidelines
