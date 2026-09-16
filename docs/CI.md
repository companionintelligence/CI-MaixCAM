# Running CI for this repo

Automatic workflow triggers in this repository are **gated**: pushing does not
start a GitHub-hosted run any more. Checks run on local hardware, and the
workflows that remain are started deliberately.

Why: GitHub Actions was costing the org $563/month, almost all of it hosted
compute for checks that run just as well on hardware we already own.

Starting a gated workflow needs the [`gh` CLI](https://cli.github.com) and push
access. `--ref` matters - the workflow file is read from that branch, so a
workflow that only exists on your feature branch must be dispatched against it.

Full cross-repo runbook: `CI-Local-CICD/RUNBOOK.md` (regenerate with
`ci-local docs`). This file is generated - do not hand-edit.

---

Default branch: `main`

### Test locally

_No local checks detected._

### Run a check workflow on GitHub

_No workflows configured._ The seven previously listed here (`build_maixcam.yml`,
`build_maixcam_dev.yml`, `build_maixcam_main_pr.yml`, `release_maixcam.yml`,
`release_other_linux.yml`, `sync_gitee.yml`, `trigger_wiki.yml`) were
unattributed vendored copies of [sipeed/MaixPy](https://github.com/sipeed/MaixPy)'s
own build/release/sync CI — not this app's CI — and have been removed. See
[`docs/License-FAQ.md`](License-FAQ.md#where-did-the-maixpy-build-release-and-sync-workflows-go)
for why.
