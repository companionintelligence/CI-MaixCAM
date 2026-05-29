# ANTIGRAVITY.md — CI-MaixCAM

## Context

**CI-MaixCAM** — **Device** layer of the Companion Intelligence platform (Lifescope Inc).

Architecture: `CI-Engineering/architecture/architecture.md`
Roadmap: `CI-Engineering/architecture/roadmap.md`

## Purpose

Companion Intelligence integration for the MaixCAM vision capture device. Streams vision data and activity to CI-Server.

## Stack

- Python / MaixPy (device SDK)
- OpenCV / vision pipeline

## Commands

```bash
pip install -r requirements.txt
python main.py
pytest
```

## Rules

- Package manager: do not switch or mix.
- Destructive git operations (`reset --hard`, `clean -f`) require explicit user confirmation.
- Commits reference CI-Engineering issues.
- All content is **private and confidential** — Property of Lifescope Inc.
