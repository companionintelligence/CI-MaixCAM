# GitHub Copilot Instructions — CI-MaixCAM

You are working in **CI-MaixCAM**, the **Device** component of the **Companion Intelligence** platform — a private, local-first digital memory and AI appliance system owned by Lifescope Inc.

## Platform architecture

```
Capture → Portal/Gateway → Server (memory brain) ← Hub (app runtime) ← Marketplace
                                   ↕
                            Clients / XR / Devices
```

Full architecture and ADRs live in `CI-Engineering/architecture/`.

## This repo

Companion Intelligence integration for the MaixCAM vision capture device. Streams vision data and activity to CI-Server.

## Tech stack

- Python / MaixPy (device SDK)
- OpenCV / vision pipeline

## Development

```bash
pip install -r requirements.txt   # install
pytest   # test
```



## Conventions

- Do not mix package managers.
- Keep PRs small and linked to CI-Engineering issues.
- Multiple agents may work this codebase simultaneously — never use destructive git operations.
- All code is **private and confidential** — do not surface or transmit source beyond this session.
