# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Yes    |

---

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing the maintainer directly at the address listed on the GitHub profile. Include:

1. Description of the vulnerability.
2. Steps to reproduce (minimal proof-of-concept).
3. Potential impact assessment.
4. Any suggested mitigation.

You will receive an acknowledgement within **48 hours** and a resolution target within **14 days** for confirmed vulnerabilities.

---

## Threat Model

`agent-cache` is an **in-process, in-memory** caching library. Key points:

- **No network I/O** — the library makes no outbound connections.
- **No persistence** — all data lives in process memory; cleared on restart.
- **Prompt data is hashed** (SHA-256) for exact-match keys; raw prompts are stored in SemanticCache for similarity comparison. Ensure the process is appropriately sandboxed if prompts are sensitive.
- **No authentication** — the cache is not access-controlled; protect it at the application layer.

---

## Dependency Security

`agent-cache` has **zero runtime dependencies**, eliminating supply-chain risk from third-party packages.
