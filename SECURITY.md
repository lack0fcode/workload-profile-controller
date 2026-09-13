# Security

This document describes the security model, operational security recommendations and security boundaries of Workload Profile Controller.

The controller is designed to perform infrastructure state changes safely, but it is not intended to replace the security controls of the underlying infrastructure platform.

---

# Security goals

The security design focuses on:

* protecting infrastructure credentials;
* preventing accidental infrastructure mutations;
* validating infrastructure state before transitions;
* avoiding ambiguous resource resolution;
* using TLS for backend communication;
* minimizing provider-specific privileges;
* failing closed when transitions cannot be completed safely;
* keeping secrets outside the source repository.

---

# Security boundaries

The project has three important security boundaries:

```text
User / Operator
       │
       ▼
      CLI
       │
       ▼
     Core
       │
       ▼
   Backend API
       │
       ▼
 Infrastructure
```

The controller does not attempt to become an authentication or authorization system for the infrastructure itself.

Authentication and authorization remain responsibilities of the underlying backend.

For example, with Proxmox:

```text
Workload Profile Controller
          │
          │ API token
          ▼
      Proxmox API
          │
          ▼
    Proxmox permissions
          │
          ▼
     Infrastructure
```

The controller should therefore be granted only the permissions required for its intended workload.

---

# Secrets

Credentials must never be stored in source code or workload configuration files.

Sensitive values include:

* API token secrets;
* passwords;
* private keys;
* authentication credentials;
* provider access tokens;
* other infrastructure credentials.

The recommended development configuration is an environment file:

```text
.env
```

The repository's `.gitignore` excludes `.env`.

---

# Environment variables

The Proxmox backend reads sensitive connection information from environment variables.

For example:

```text
PVE_PROXMOX_USER=controller-user@pve
PVE_PROXMOX_TOKEN_NAME=controller
PVE_PROXMOX_TOKEN_SECRET=<secret>
```

The actual secret must never appear in:

* Git;
* YAML configuration;
* source code;
* test fixtures;
* README examples;
* screenshots;
* issue reports;
* pull requests.

Use placeholder values in documentation and examples.

---

# `.env` files

A local `.env` file is convenient for development.

Example:

```text
PVE_PROXMOX_HOST=proxmox.example.internal
PVE_PROXMOX_NODE=pve-node-01
PVE_PROXMOX_USER=controller-user@pve
PVE_PROXMOX_TOKEN_NAME=controller
PVE_PROXMOX_TOKEN_SECRET=<secret>
PVE_PROXMOX_VERIFY_TLS=true
```

The real `.env` file should remain local.

Before committing changes, verify that it is ignored:

```bash
git status --ignored
```

Never use `git add -f .env`.

---

# Secret rotation

If a credential is accidentally exposed:

1. Revoke or rotate the credential immediately.
2. Create a replacement credential.
3. Update the deployment configuration.
4. Verify that the old credential is no longer valid.
5. Investigate where the credential was exposed.
6. Remove the exposed credential from any public or shared location.

Removing a secret from the latest Git commit is not sufficient if it has already been pushed to a remote repository.

Treat an exposed credential as compromised.

---

# Proxmox API tokens

The Proxmox backend uses API-token authentication.

The recommended deployment model is to create a dedicated identity for the controller rather than using an administrator account.

For example:

```text
controller identity
        │
        └── dedicated API token
```

The controller should not use a personal administrator credential.

---

# Principle of least privilege

The Proxmox identity used by the controller should receive only the permissions necessary to:

* discover the resources it manages;
* read their state;
* start managed resources;
* request graceful shutdown of managed resources;
* monitor the resulting tasks.

Do not grant unrestricted administrative privileges unless they are genuinely required by the deployment.

The exact Proxmox ACL configuration depends on the resources and permissions available in the target environment.

Permissions should therefore be reviewed against the actual deployment rather than copied blindly from an example.

---

# Resource scope

The controller should be granted access only to the resources it is intended to manage.

If the underlying infrastructure supports resource-specific permissions, prefer restricting access to those resources rather than granting permissions across the entire infrastructure.

This reduces the potential impact of:

* configuration mistakes;
* compromised credentials;
* unauthorized use of the controller;
* software vulnerabilities.

---

# TLS

Communication with the Proxmox API should use HTTPS.

TLS certificate verification is enabled by default:

```text
PVE_PROXMOX_VERIFY_TLS=true
```

This prevents the controller from blindly trusting an arbitrary server.

---

# Custom CA certificates

Private infrastructure may use an internal certificate authority.

In that case, configure the backend with the appropriate CA certificate:

```text
PVE_PROXMOX_CA_FILE=./config/pve-root-ca.pem
```

The CA file should contain only the public CA certificate required to validate the server certificate.

Never place a CA private key in the project.

---

# TLS server name

The network connection host and TLS server name may be different.

For example:

```text
PVE_PROXMOX_HOST=192.0.2.10
PVE_PROXMOX_TLS_SERVER_NAME=pve-node-01.example.internal
```

The first value determines where the TCP connection is established.

The second value is used for TLS server-name validation.

This distinction is useful when infrastructure is accessed through an IP address while the server certificate identifies a DNS name.

---

# Disabling TLS verification

Disabling certificate verification is strongly discouraged.

Avoid:

```text
PVE_PROXMOX_VERIFY_TLS=false
```

in production.

Disabling TLS verification can allow a man-in-the-middle attacker to impersonate the infrastructure API.

If certificate validation fails, the preferred solution is to correct the CA or server-name configuration rather than disabling verification.

---

# Resource identity security

The Proxmox backend resolves resources using exact names.

It does not perform:

* fuzzy matching;
* substring matching;
* case-insensitive matching;
* regular-expression matching;
* arbitrary fallback resolution.

This is a security property as well as a correctness property.

For example, if the configuration specifies:

```text
compute
```

the backend must not silently select:

```text
compute-test
```

or:

```text
compute-old
```

A missing or ambiguous resource causes an error.

---

# Ambiguous resources

If multiple infrastructure resources have the same configured name, the backend rejects the resolution.

For example:

```text
QEMU:
  compute

LXC:
  compute
```

The controller does not select one arbitrarily.

This prevents an ambiguous configuration from becoming an unexpected infrastructure mutation.

---

# Transition safety

Security is not limited to credentials.

Because the controller performs infrastructure mutations, incorrect state transitions can also create operational risk.

The controller therefore applies several safety rules.

---

## Validate before mutation

The expected source profile must match the observed infrastructure state before a transition begins.

For example:

```text
Expected:

monitoring = RUNNING
compute    = STOPPED
```

If the actual state differs, the controller rejects the transition.

No transition should begin from an unknown or unexpected state.

---

## Resolve before mutation

Resources required by the target profile must be resolvable before the first state-changing operation.

This prevents a transition such as:

```text
STOP A
STOP B
START C
START D
```

from discovering that `D` does not exist only after several mutations have already occurred.

---

# Stop-before-start

When a transition requires resources to be stopped before another resource can start, the controller confirms the stopped state before continuing.

Conceptually:

```text
STOP conflicting resource
          │
          ▼
    Confirm STOPPED
          │
          ▼
     START target
```

This reduces the risk of simultaneous operation of mutually exclusive workloads.

---

# Operation confirmation

A successful API request is not automatically treated as a successful infrastructure transition.

The backend monitors asynchronous operations and the controller verifies the resulting resource state.

For example:

```text
START request
     │
     ▼
Backend task
     │
     ▼
Task completion
     │
     ▼
Resource status
     │
     ├── RUNNING → success
     │
     └── anything else → failure
```

---

# No forced shutdown

The controller does not use forced shutdown as a normal recovery mechanism.

If graceful shutdown does not complete within the configured timeout, the operation fails.

This avoids silently escalating an operational problem into a potentially destructive action.

---

# Fail-closed behavior

The controller favors failure over guessing.

If a transition fails after infrastructure mutation has started, the controller enters:

```text
LOCKED
```

The controller does not assume that the desired profile was reached.

This is intentional.

For infrastructure automation, incorrectly claiming success can be more dangerous than stopping and requiring human investigation.

---

# Partial transitions

The controller does not currently attempt automatic rollback.

For example:

```text
STOP A       ✓
STOP B       ✓
START C      ✓
START D      ✗
```

The resulting infrastructure may be partially transitioned.

Instead of attempting an automatic rollback under uncertain conditions, the controller enters the locked state.

The operator can then inspect the actual infrastructure state and determine the appropriate recovery action.

---

# Reconciliation

Reconciliation is intentionally observational.

It can determine:

```text
Infrastructure state
        │
        ▼
Matches profile A ──► profile A
Matches profile B ──► profile B
No exact match ─────► LOCKED
```

It does not automatically start or stop resources.

This prevents recovery logic from making unexpected infrastructure changes.

---

# Controller state

The controller uses the following states:

```text
IDLE
TRANSITIONING
LOCKED
```

The `LOCKED` state is a safety boundary.

Once the controller is locked, normal transitions are rejected until the state is explicitly resolved.

---

# CLI security

The CLI should not expose secrets as command-line arguments.

Avoid interfaces such as:

```bash
wpc --token-secret "my-secret"
```

Command-line arguments may be visible through process inspection, shell history or other system interfaces.

Credentials should instead be provided through the configured environment or an appropriate secret-management mechanism.

---

# Logs and diagnostics

Logs and error messages should not contain:

* API token secrets;
* passwords;
* private keys;
* authorization headers;
* complete authentication credentials.

Diagnostic information should provide enough context to troubleshoot failures without exposing sensitive information.

For example, this is preferable:

```text
Proxmox API request failed: HTTP 401 Unauthorized
```

rather than logging an authentication header containing the token.

---

# Configuration files

Workload configuration is not considered secret by default.

A profile such as:

```yaml
profiles:
  profile1:
    running:
      - monitoring
    stopped:
      - compute
```

does not contain credentials.

However, configuration can still reveal infrastructure information.

Before publishing configuration examples, review them for:

* internal hostnames;
* IP addresses;
* internal resource names;
* organization-specific information;
* operational details that should remain private.

The repository should contain sanitized examples rather than real deployment configuration.

---

# Repository security

Before publishing the project, verify that the repository does not contain:

* `.env` files;
* API token secrets;
* passwords;
* private keys;
* internal hostnames;
* internal IP addresses;
* personal usernames;
* infrastructure-specific identifiers that should remain private.

Useful local checks include:

```bash
git status
```

and repository-wide searches for common credential patterns.

Secrets should be prevented from entering Git rather than removed after publication.

---

# Dependency security

The project depends on third-party Python packages.

Dependencies should be:

* kept reasonably up to date;
* reviewed before upgrades;
* installed from trusted package sources;
* tested after upgrades.

The development environment currently uses:

* PyYAML;
* python-dotenv;
* pytest;
* Ruff.

Production deployments should install only the dependencies required by the application.

---

# Backend trust model

The controller trusts the backend implementation to correctly translate abstract operations into infrastructure operations.

Therefore, backend implementations are security-sensitive components.

A new backend should be reviewed for:

* authentication;
* authorization;
* TLS;
* resource resolution;
* state mapping;
* operation confirmation;
* timeout behavior;
* error handling.

A backend must not silently broaden the meaning of a resource identifier.

---

# WebUI considerations

A future WebUI must not reimplement transition logic independently.

The WebUI should call the same application/controller layer used by the CLI.

The intended architecture is:

```text
CLI ────────┐
            │
            ▼
       Application
            │
            ▼
        Controller
            │
            ▼
         Backend

WebUI ──────┘
```

This prevents different interfaces from implementing inconsistent safety rules.

A future WebUI will additionally require its own authentication and authorization model.

The existence of the current CLI security model does not automatically make a future WebUI safe for network exposure.

---

# Network exposure

The controller should not be exposed directly to an untrusted network without an appropriate authentication and authorization layer.

In particular:

* do not expose administrative control endpoints publicly;
* do not assume network location is sufficient authentication;
* protect future WebUI endpoints;
* use HTTPS where appropriate;
* restrict access through network controls where possible.

The current CLI does not provide a network service.

---

# Threat model

The controller is primarily designed to protect against:

* accidental workload conflicts;
* incorrect profile transitions;
* ambiguous resource selection;
* incomplete asynchronous operations;
* configuration mistakes;
* accidental credential commits;
* unsafe infrastructure assumptions.

It is not intended to protect against:

* a fully compromised Proxmox host;
* a malicious administrator with infrastructure-level privileges;
* a compromised operating system running the controller;
* a malicious backend implementation;
* a compromised credential store;
* arbitrary host-level attacks.

The underlying infrastructure remains part of the trusted computing base.

---

# Security assumptions

The controller assumes that:

1. The operating system running the controller is trusted.
2. The backend API endpoint is correctly configured.
3. TLS certificate validation is correctly configured.
4. Backend credentials are protected by the deployment environment.
5. The configured workload profiles accurately represent the intended operational states.
6. The infrastructure backend correctly reports resource states.
7. Operators have appropriate authorization to perform the requested transitions.

Violating these assumptions can invalidate the controller's safety guarantees.

---

# Security checklist for deployment

Before deploying the controller:

* [ ] Create a dedicated backend identity.
* [ ] Create a dedicated API token.
* [ ] Apply least-privilege permissions.
* [ ] Restrict access to managed resources where possible.
* [ ] Enable TLS verification.
* [ ] Configure the correct CA certificate.
* [ ] Configure the correct TLS server name.
* [ ] Store credentials outside Git.
* [ ] Verify `.env` is ignored.
* [ ] Review configuration for internal information.
* [ ] Test resource resolution.
* [ ] Run transition plan.
* [ ] Verify graceful shutdown behavior.
* [ ] Verify task timeout behavior.
* [ ] Verify failure/locked-state behavior.
* [ ] Review logs for accidental secret exposure.
* [ ] Keep dependencies updated.

---

# Security reporting

If you discover a security vulnerability in the project, avoid publishing sensitive details in a public issue before the vulnerability has been assessed.

Once the project has a dedicated security contact, security reports should be directed through that channel.

Until then, maintainers should treat reports involving credentials, authentication bypasses, unauthorized infrastructure operations or remote code execution as security-sensitive.

---

# Security principle

The central security principle of Workload Profile Controller is:

> **Infrastructure automation should fail safely rather than guess.**

The controller therefore prefers:

```text
unknown state → stop
ambiguous resource → stop
unexpected state → stop
failed transition → lock
invalid configuration → reject
```

rather than attempting to infer what the operator intended.

This principle is fundamental to the design of the project.
