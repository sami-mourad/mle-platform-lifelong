# Security Policy

## Supported versions

Security fixes are applied to the latest tagged release and `main`.

## Reporting a vulnerability

After the repository is public, report vulnerabilities through a private GitHub security advisory rather than a public issue. Include the affected path, reproduction steps, impact, and any suggested mitigation.

## Local-development boundary

`.env.example` and Docker Compose contain non-production development values. They must not be reused in a shared or internet-facing environment.

A real deployment requires:

- secret management and workload identity;
- TLS and authenticated service boundaries;
- private database and object-store networking;
- least-privilege IAM and audited administrative access;
- encryption at rest and in transit;
- signed and verified release artifacts;
- PII classification, retention, deletion, and audit policies;
- removal of development-only fallback controls;
- image scanning, dependency review, and patch SLAs;
- backup, restore, and incident-response procedures.

This release does not claim that those production controls are implemented.
