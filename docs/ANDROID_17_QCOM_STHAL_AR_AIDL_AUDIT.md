# PE-Reborn Android 17 — row 177: old Qualcomm AudioReach/PAL Sound Trigger versus AIDL

**Date:** 2026-11-07. Future independent PixelExperience-Reborn product: POCO F5 Pro / Redmi K60 `mondrian`, SM8475 / Qualcomm `taro`.

## Decision

**Do NOT ship the old PE `vendor/qcom/opensource/audio-hal/st-hal-ar` `seventeen` source as Android17 SoundTrigger3 HAL.** This is an older Qualcomm **PAL-backed but legacy Sound Trigger C interface** implementation from 2024, distinct from the modern Qualcomm-derived SoundTrigger3 **stable AIDL V1** in Sony-hosted `AUDIO.LA.10.0.r1`. The old PAL-based version is more modern than old LSM/GCS `st-hal` (row176), but that alone is **not** the newest interface generation.

The source-only modern **six-repo** AudioReach candidate was already placed and CI-verified in independent PE manifest `aosp17_pe_p2_qcom_audio_aidl_candidate.xml` (row176, [CI #42327702807](https://github.com/PixelExperience-Reborn/vendor_qcom_opensource_audio-hal_st-hal/actions/runs/42327702807)). Do not substitute either 2024 `st-hal-ar` or a newer-dated legacy fork into that candidate. Its strict Sony-hosted Qualcomm-derived `AUDIO.LA.10.0.r1` pins are intentionally nondefault and must be promoted only with matched Xiaomi vendor ABI/ADSP/ACDB/PAL, Soong/NDK, VINTF and real device tests.

## Exact source snapshots

| Role | Git commit/tree | Why checked |
| --- | --- | --- |
| Historical `PixelExperience-Reborn/vendor_qcom_opensource_audio-hal_st-hal-ar` `seventeen` | `420362bced12aa266fbf73be76ee440b8341829f` / `4e0987fea0b25cc46803456cd8e39c616d7602df`, dated 2024-01-04 | 10 legacy AudioReach source files with `Android.mk`, `SoundTriggerDevice.cpp`, `SoundTriggerSession.cpp` and PAL/Audio HAL callback contract |
| Historical `PixelExperience-Reborn/vendor_qcom_opensource_audio-hal_st-hal` `seventeen` | `68d8705deab99367a1c4022470feb7a4bf8cc785` / `1f74e1622de15d71d8999e6969932a1f0bce2f4a` | Previous row176 2023 C/GCS/LSM variant disabled when `TARGET_USES_QCOM_AUDIO_AR=true` |
| **Newer-dated** AOSPA `android_vendor_qcom_opensource_audio-hal_st-hal-ar` `calcite-8650` | `1e5357da99c4080a9369ee55a4641a460b45b077` / `40ab7cd6cf67664130bc93974f3a0b286e233952`, dated 2026-09-16 | Modern Soong build system/null-pointer fix, **but it still exports legacy `sound_trigger.primary.%s` and `SoundTriggerDevice.cpp`**. Newer date/Soong file is not equivalent to a SoundTrigger3 AIDL implementation. This fork is reference-only and `8650` is not proof of SM8475 compatibility |
| Sony-hosted Qualcomm-derived `vendor-qcom-opensource-audio-hal-st-hal-ar` `aosp/AUDIO.LA.10.0.r1` | `1dcb1275256b3f43b78d342d623870324a831720` / `d47390edeaf35ee6b50d15b88e9f5537f372174e` | Real `libsoundtriggerhal.qti` **AIDL V1** `ISoundTriggerHw/default` NDK Binder/PAL factory; 19 source files |
| Sony-hosted Qualcomm-derived `vendor-qcom-opensource-audio-hal-primary-hal-ar` `aosp/AUDIO.LA.10.0.r1` | `b071e74ead44a7aecee69969003b902632cd4ab3` / `c78551f4c27dab685e396cd8996c1458b724787d`, Aug 2026 | Android17 primary Audio Core V3 and Effects V4, `audiohalservice.qti` dynamic HAL factory |
| Independent PE-selected `hardware_interfaces` | `735e364cbdd00b0d6e4dc33ea0866dbb6d971a11` / `adad11a145a3ecd709642f720a53f5a923fce754` | Official AOSP17 `android.hardware.soundtrigger3` frozen AIDL V1 through **V4** |

## Evidence: the old AudioReach source still uses the legacy hardware HAL

`Android.mk` guards selection by `BOARD_SUPPORTS_OPENSOURCE_STHAL=true`, `TARGET_USES_QCOM_MM_AUDIO=true`, `TARGET_USES_QCOM_AUDIO_AR=true` and excludes `AUDIO_USE_STUB_HAL=true`. The module is **`sound_trigger.primary.$(TARGET_BOARD_PLATFORM)`**, built from `SoundTriggerDevice.cpp` and `SoundTriggerSession.cpp`, linked to `libar-pal`, `libhidlbase`, and optionally `vendor.qti.hardware.ListenSoundModel@1.0`.

`SoundTriggerDevice.cpp` creates a native **`sound_trigger_hw_device`**, declares the old `sthal_prop_api_version` callback contract, handles `stdev_load_sound_model` and `stdev_start_recognition`, optionally registers an LSM **HIDL** service, and uses `dlsym` for the Audio HAL side `check_init_audio_extension`. `SoundTriggerSession.cpp` translates legacy C sound model/recognition data to PAL. That is a PAL backend under a **legacy HAL front end**, *not* a modern AIDL/NDK Binder entrypoint.

A Sony-hosted Qualcomm-derived `AUDIO.LA.10.0.r1` checkout changes the front end entirely: `libsoundtriggerhal.qti` exports `createISoundTriggerFactory()`, registers native `android.hardware.soundtrigger3.ISoundTriggerHw/default`, declares **AIDL version 1** and connects to PAL. A modern `audiohalservice.qti` must be configured to load that factory. We need **AIDL V1 to frozen V4 framework compatibility**, not an assumption that the vendor implements V4.

AOSPA September 2026 `calcite-8650` is newer by date and has a Soong `Android.bp`, but its `target_board_platform_cc_library_shared` names the binary **`sound_trigger.primary.%s`** and continues using the old `SoundTriggerDevice.cpp`. Newer *timestamp*, *Soong syntax*, or a newer SoC class are insufficient to select the best Android17 interface implementation. Compare actual exported APIs and matched Xiaomi hardware.

## Board-specific and safety requirements

- `mondrian` is SM8475 `taro`-family, **not** `calcite-8650` or a Sony product. Stock Xiaomi vendor soundtrigger service, ADSP topology, codec/mixer controls, sound model ABI, audio policy and microphone arrays are **not yet verified**.
- Do not install old `sound_trigger.primary.*` alongside Qualcomm SoundTrigger3 AIDL V1, even if a compatibility fallback exists in AOSP17 `SoundTriggerMiddleware`. Preserve official `hardware/interfaces` AIDL and `frameworks/av` owners. Do not enable optional ListenSoundModel HIDL without proof of need and access control.
- Verify current AIDL `ISoundTriggerHw/default` FCM/VINTF, PAL/AGM/graph service source+ABI, ADSP firmware, Audio Core V3/Effects V4, `audiohalservice.qti` dynamic factory config, SELinux, mic/hotword privacy/permissions, low-power wake and SSR, Bluetooth SCO changes, voice-call concurrency, CTS/VTS and independent device boot.
- New Qualcomm-derived source is a **nondefault preview** at six immutable Git commits (row176); it is not a working audio HAL. LF52406 LineageOS device trees are only exceptional **read-only hardware evidence**, not the PE-Reborn implementation base.

## Deliverables

Dedicated `audit/a17-qcom-audioreach-legacy-vs-aidl-20261107` branch: this comparative audit, pinned source checker and GitHub Actions. Working PE manifest rejects old historical `vendor/qcom/opensource/audio-hal/st-hal-ar` from **active reviewed stages**, and only permits its path under the strictly pinned six-project Sony-hosted AudioReach preview (with a distinct repository owner and immutable commit). Two adversarial tests enforce this. Matrix row177 records the outcome. Original `seventeen`, main `default.xml`, firmware/device/product and installed HAL remain untouched.

**No Soong/audio build, runtime Binder service or physical `mondrian` audio/hotword testing was performed.**
