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

**Build MaixCAM** — `build_maixcam.yml`

```bash
gh workflow run build_maixcam.yml --repo companionintelligence/CI-MaixCAM --ref main
```

**Build MaixCAM Dev branch** — `build_maixcam_dev.yml`

```bash
gh workflow run build_maixcam_dev.yml --repo companionintelligence/CI-MaixCAM --ref main
```

**Build MaixCAM PR** — `build_maixcam_main_pr.yml`

```bash
gh workflow run build_maixcam_main_pr.yml --repo companionintelligence/CI-MaixCAM --ref main
```

**sync code to gitee** — `sync_gitee.yml`

```bash
gh workflow run sync_gitee.yml --repo companionintelligence/CI-MaixCAM --ref main
```

**trigger wiki** — `trigger_wiki.yml`

```bash
gh workflow run trigger_wiki.yml --repo companionintelligence/CI-MaixCAM --ref main
```

### Cut a release

**Relase MaixPy for MaixCAM** — `release_maixcam.yml`

```bash
gh workflow run release_maixcam.yml --repo companionintelligence/CI-MaixCAM --ref main
```

**Relase MaixPy for Linux** — `release_other_linux.yml`

```bash
gh workflow run release_other_linux.yml --repo companionintelligence/CI-MaixCAM --ref main
```
