# License FAQ

### Can you summarize what Companion MaixCAM's license allows?

The license grants free rights to use, modify, and redistribute Companion MaixCAM source code for personal or nonprofit purposes. The intent is to stay permissive for those uses while limiting commercial abuse of Companion Intelligence products.

Companion MaixCAM is Companion Intelligence's integration for the [Sipeed MaixCAM](https://wiki.sipeed.com/hardware/en/maixcam/index.html) vision capture device — it streams vision frames and activity data from MaixCAM hardware to Companion Memory (CI-Server) using the MaixPy framework.

Companion MaixCAM uses the [PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0). The full text is in [`LICENSE.md`](../LICENSE.md).

### What freedoms do you have as a Companion MaixCAM user?

If you use Companion MaixCAM for personal or nonprofit purposes, you can view, modify, and redistribute the source under the same license terms, subject to the PolyForm Noncommercial restrictions.

### Can I fork Companion MaixCAM?

Yes. For noncommercial use, you can fork, modify, and redistribute Companion MaixCAM under the same license.

### Can I contribute to Companion MaixCAM?

Yes. Open a pull request on this repository.

### Can I sell Companion MaixCAM?

No. Selling Companion MaixCAM, including cloud-hosted instances, appliances that ship it, or paid support for those products, is not permitted. For commercial partnership questions, email partner@companionintelligence.com.

### Where did `MaixPy_docs/` and `MaixPy_examples/` go?

This repo used to vendor a local copy of Sipeed's MaixPy documentation and examples for reference. That copy carried no license or attribution markers of its own, which isn't compatible with clearing this repo for a PolyForm Noncommercial release — Sipeed's docs and examples are [Apache-2.0](https://github.com/sipeed/MaixPy), and a vendored copy needs that license and notice to travel with it. Rather than reproduce Sipeed's attribution requirements here, this repo now links to [sipeed/MaixPy](https://github.com/sipeed/MaixPy) directly. Companion MaixCAM's own product code (`src/`) is unaffected — it only ever depended on the MaixPy SDK at runtime, not on the vendored docs/examples copy.

### Where did the MaixPy build, release, and sync workflows go?

`.github/workflows/` used to carry seven files — `build_maixcam.yml`, `build_maixcam_dev.yml`, `build_maixcam_main_pr.yml`, `release_maixcam.yml`, `release_other_linux.yml`, `sync_gitee.yml`, and `trigger_wiki.yml` — copied near-verbatim from [sipeed/MaixPy](https://github.com/sipeed/MaixPy)'s own CI, with no attribution to Sipeed at all. They built and published the *MaixPy SDK itself* (cloning `sipeed/MaixCDK`, running `setup.py bdist_wheel`, publishing the result to PyPI as `MaixPy`), pushed to Sipeed's own Gitee mirror, and dispatched update events to Sipeed's own wiki repo. None of that is something this app — a MaixPy *client*, not the SDK — ever needed, and none of it could actually run here: the `setup.py`, `run.sh`, and `tools/os/` scripts those workflows invoke were never part of this repo, only of the upstream project they were copied from. Same reasoning as `MaixPy_docs/`/`MaixPy_examples/` above: Sipeed's Apache-2.0 terms are for a copy that's genuinely used and credited, not dead CI wired to the original project's own infrastructure. Removed rather than attributed. If this app ever needs its own build automation, it should be written for what it is, not inherited from what it was copied out of.

### Does this license apply to the rest of Companion Intelligence?

Companion Portal stays a separate commercial product — this license does not apply to it.

Companion Hub, Companion Memory, Companion Marketplace, Companion OS, Companion Capture, Companion Browser Extension, Companion OMI, Companion Mentra, Companion Even Realities, Companion Pebble, and Companion Home Assistant Voice PE use the same PolyForm Noncommercial terms in their own repositories.

Companion Pipe is still under legal review for third-party licensing terms in code it bundles — don't assume it's covered by this FAQ until that review lands.

### Unsure whether your use case is allowed?

Email support@companionintelligence.com.
