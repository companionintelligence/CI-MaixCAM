# CLAUDE.md — CI-MaixCAM

> **Private & Confidential — Property of Lifescope Inc. Do not distribute.**

## Platform role

**CI-MaixCAM** sits in the **Device** layer of the Companion Intelligence platform.

Architecture: `CI-Engineering/architecture/architecture.md`
Roadmap: `CI-Engineering/architecture/roadmap.md`
Issues: <https://github.com/companionintelligence/CI-Engineering/issues>

## What this repo does

Companion Intelligence integration for the MaixCAM vision capture device. Streams vision data and activity to CI-Server.

## Stack

- Python / MaixPy (device SDK)
- OpenCV / vision pipeline

## Key commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server / service
python main.py

# Run tests
pytest

# Build for production
# flash via MaixPy toolchain
```

## Package manager

**pip** — use exclusively; do not mix with npm/yarn/pnpm/bun unless the repo explicitly requires it.

## Cross-repo connections

- Vision frames stream to CI-Server
- Device registered via CI-Server /devices API



## Multi-agent safety

Multiple AI agents work these repos in parallel. Never use `git reset --hard`, `git clean -f`, or any destructive git command without explicit confirmation from the user.

## Confidentiality

Private & Confidential — Property of Lifescope Inc. Do not distribute.
