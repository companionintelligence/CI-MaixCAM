# Scan-to-provision — design note

> **Status: not implemented.** This is a record of the opportunity and of
> what stands in the way of it. No code in `src/` scans a QR code today.
> Written 2026-08-26.

CI-MaixCAM is the one device on the Companion Intelligence platform that can
already decode a QR code and does not use that ability for anything. Every
other device gets its Wi-Fi credentials and its CI-Server endpoint typed in
by hand somewhere. This one has a camera, an NPU, a QR decoder in the SDK,
and a touchscreen — the gesture of pointing it at a code on a phone screen is
the shipped UX on this hardware, not something we would be inventing.

## What the hardware already does

Two working examples ship in this repo, both decoding to a payload string and
four corner points:

- `MaixPy_examples/vision/image_basic/find_qrcodes.py` — `img.find_qrcodes()`
  on a 320x240 camera, then `q.payload()` and `q.corners()` per result.
- `MaixPy_examples/vision/image_basic/find_qrcodes_faster.py` — the faster
  path, `image.QRCodeDetector().detect(img)` on a 320x224 camera, with
  per-frame `detect use N ms` timing already printed.

And the stock vendor Settings app **already provisions Wi-Fi by scanning a
QR code**. From `MaixPy_docs/doc/en/network/network_settings.md:11`:

> After powering on, enter the `Settings` application and select the `WiFi`
> function. You can connect by sharing a `WiFi QR code` from your phone or by
> generating a QR code at [maixhub.com/wifi](https://maixhub.com/wifi) and
> scanning it.

So the user gesture is proven on this exact hardware. What is missing is our
side of it: getting our own endpoint and enrolment claim onto the device the
same way, and getting them into a file the app actually reads.

## The three real blockers

**1. `maix.network.wifi` is never imported anywhere under `src/`.**
The only occurrence of the string `wifi` in the whole of `src/` is the config
default `"wifi_enabled": True` in `src/utils/config.py`. There is no code that
associates with an access point. The SDK API exists and is documented in
`MaixPy_docs/doc/en/network/network_settings.md` (`network.wifi.Wifi()`,
`w.connect(SSID, PASSWORD, wait=True, timeout=60)`, `w.get_ip()`); nothing in
this repo calls it. This is `PROJECT_PLAN.MD` step 14.1, still unchecked.

**2. The uploader has no CI-Server client.**
`src/network/uploader.py` has the full shape of an upload pipeline — queue,
worker thread, batching, retry counters, stats — but the transport is
`_mock_http_post()`, whose own comment says a real implementation "would use
libraries like urllib or requests". It posts nowhere. It also knows nothing
about CI-Server specifically: no device registration, no `/devices` enrolment,
no auth exchange. A scanned endpoint would have nothing to hand to.

**3. The config path drift — fixed, and it had to be fixed first.**
Until this note's companion commit, `src/setup_screen.py` and `src/main.py`
used `/sd/companion_config.json` while `src/utils/config.py` used
`/sd/config/app_config.json`. Everything `Config` wrote — including the
network settings a provisioning scan would target — landed in a file no other
component ever opened. Writing scanned values into a file nothing reads would
have been worse than not scanning at all: it looks like it worked. All three
sites now share `CONFIG_PATH` from `src/utils/paths.py`.

## What the setup screen would have to grow

`src/setup_screen.py` is currently thirteen AI-model checkboxes and four
buttons, and nothing else. It contains **zero** references to network,
endpoint, url, wifi, api_key or server — not one, case-insensitive, across
the whole file. There is no field for any of the values provisioning would
deliver.

Meanwhile `src/utils/config.py:125-134` already declares the slots those
values belong in, and ships them empty or fake:

```python
"network": {
    "wifi_enabled": True,
    "upload_enabled": False,
    ...
    "endpoint_url": "https://api.example.com/upload",
    "api_key": "",
    "timeout_seconds": 30
}
```

`api.example.com` is not a typo to fix in passing — it is the marker that no
device has ever been pointed at a real CI-Server. Scan-to-provision is the
mechanism that would fill `endpoint_url` and the credential slot without a
human typing a URL on a touchscreen keyboard.

## Security rule for the payload

**A provisioning QR must carry a short-lived, single-use claim reference —
never a long-lived key and never a Wi-Fi PSK.**

A QR code is not a private channel. It is displayed on a screen, it gets
photographed, it survives in screenshots and camera rolls, it re-encodes
perfectly through a screen share, and anyone in the room can read it at the
same time the device does. Anything durable inside it is durable in all of
those places too.

So the payload is a pointer, not a secret:

- a claim/enrolment token that expires in minutes, is redeemable exactly
  once, and is bound to the specific device that redeems it;
- the CI-Server base URL it should be redeemed against;
- a version tag, so a future payload shape is distinguishable.

The device exchanges the claim for its own credential over TLS and stores
that credential locally; the claim is dead the moment it is used. A leaked
QR then buys an attacker nothing after the enrolment window, and a
photographed one buys nothing at all if the real device redeemed first.

The Wi-Fi PSK is the harder case and is deliberately **out of scope here**:
the vendor Settings app already handles Wi-Fi QR provisioning
(`network_settings.md:11`), so the device can be on the network before our
app ever runs. We should use that path rather than build a second one that
puts a PSK into a payload we control.

## Sequencing

Blocker 3 is done. Blockers 1 and 2 are prerequisites — a scan is only worth
implementing once there is a network to join and a server to enrol with.
The natural order is `PROJECT_PLAN.MD` step 14.1 (`NetworkManager`), then a
real transport in `src/network/uploader.py` with CI-Server enrolment, then
the scan as the input method that feeds both.
