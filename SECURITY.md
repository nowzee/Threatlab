# Security Policy

Thank you for helping keep **Threatlabs** secure. This project currently has no dedicated security contact email and does not publish numbered releases, so we use the repository’s default branch for support and GitHub for reporting.

---

## Supported Versions

Because this project does not maintain official versioned releases, **only the default branch is supported with security fixes**:

| Target | Supported |
| ------ | --------- |
| `master` (default branch) | ✅ |
| Other branches, forks, older commits | ❌ |

When reporting, please include the **commit hash** you tested (e.g., output of `git rev-parse HEAD`) and any relevant environment details.

---

## Reporting a Vulnerability

### Preferred: GitHub Private Vulnerability Reporting
If enabled on the repository:
- Go to **Security** → **Report a vulnerability**

This is the best option because it keeps details private while we triage and patch.

### If private reporting is not available
Please open a GitHub issue with:
- Title starting with **`[SECURITY]`**
- A **high-level** description of the issue and impact

Do **not** post:
- working exploit payloads,
- step-by-step weaponized PoCs,
- credentials, tokens, or other secrets.

Ask in the issue for a private channel (we’ll reply with next steps).

---

## What to Include in Your Report

- A clear description of the vulnerability and **security impact**
- Affected component(s): `backend/`, `frontend/`, `docker-compose.yml`, etc.
- Steps to reproduce (safe/minimal PoC preferred)
- Expected vs. actual behavior
- The commit hash tested and the environment (OS, Docker setup, browser if relevant)
- Any suggested mitigation or patch ideas (optional)

---

## Response Timeline (Best Effort)

As a small project without an on-call team, we aim for:
- Acknowledgement: within **7 days**
- Initial triage: within **14 days**
- Updates: when available (goal: at least every **2 weeks** while open)

---

## Scope

### In scope
- Python/Flask backend
- Vue/TypeScript frontend
- Versioned deployment/configuration (e.g., Docker Compose)
- Database schema/scripts that are part of the repository

### Out of scope
- Purely theoretical issues with no demonstrated impact
- Volumetric DoS (network flooding)
- Social engineering

---

## Responsible Disclosure

Please avoid public disclosure until a fix is available (or we agree on a disclosure timeline). Coordinated disclosure helps protect users and operators of deployed instances.

---

## Safe Harbor

We consider security research to be authorized **in good faith** when you:
- test only against systems you own or have explicit permission to test,
- avoid accessing or exfiltrating real user data,
- avoid intentional service disruption.

---
