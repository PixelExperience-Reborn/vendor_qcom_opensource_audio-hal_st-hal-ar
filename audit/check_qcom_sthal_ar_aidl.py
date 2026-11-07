#!/usr/bin/env python3
"""Row177: exact Qualcomm PAL legacy (2024/2026) vs SoundTrigger3 AIDL source.

No HAL compilation, DSP driver firmware, vendor ABI, mic/hotword or device
operation. The Sony-hosted AUDIO.LA.10.0.r1 snapshot is a candidate only.
Args: OLD_PE_AR OLD_PE_GCS NEWER_LEGACY_2026 NEW_AIDL NEW_PRIMARY
      PE_AOSP17_INTERFACES PE_MANIFEST
"""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

OLD_AR_SHA = "420362bced12aa266fbf73be76ee440b8341829f"
OLD_AR_TREE = "4e0987fea0b25cc46803456cd8e39c616d7602df"
OLD_GCS_SHA = "68d8705deab99367a1c4022470feb7a4bf8cc785"
OLD_GCS_TREE = "1f74e1622de15d71d8999e6969932a1f0bce2f4a"
AOSPA_SHA = "1e5357da99c4080a9369ee55a4641a460b45b077"
AOSPA_TREE = "40ab7cd6cf67664130bc93974f3a0b286e233952"
MODERN_SHA = "1dcb1275256b3f43b78d342d623870324a831720"
MODERN_TREE = "d47390edeaf35ee6b50d15b88e9f5537f372174e"
PRIMARY_SHA = "b071e74ead44a7aecee69969003b902632cd4ab3"
PRIMARY_TREE = "c78551f4c27dab685e396cd8996c1458b724787d"
IFACE_SHA = "735e364cbdd00b0d6e4dc33ea0866dbb6d971a11"
IFACE_TREE = "adad11a145a3ecd709642f720a53f5a923fce754"
OLD_PATH = "vendor/qcom/opensource/audio-hal/st-hal-ar"
OLD_REPO = "vendor_qcom_opensource_audio-hal_st-hal-ar"


def require(ok, msg):
    if not ok:
        raise RuntimeError(msg)


def git(repo, *args):
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True,
        stderr=subprocess.PIPE).strip()


def pin(root, ref, sha, tree, label):
    actual = git(root, "rev-parse", f"{ref}^{{commit}}")
    require(actual == sha, f"{label}: commit changed {actual}")
    tree_id = git(root, "rev-parse", f"{actual}^{{tree}}")
    require(tree_id == tree, f"{label}: tree changed {tree_id}")
    return actual


def show(root, commit, filename):
    return git(root, "show", f"{commit}:{filename}")


def paths(root, commit):
    return git(root, "ls-tree", "-r", "--name-only", commit).splitlines()


def archived_pe_pal(root):
    sha = pin(root, "refs/remotes/origin/seventeen",
              OLD_AR_SHA, OLD_AR_TREE, "PE 2024 PAL legacy STHAL")
    make = show(root, sha, "Android.mk")
    device = show(root, sha, "SoundTriggerDevice.cpp")
    session = show(root, sha, "SoundTriggerSession.cpp")
    require(len(paths(root, sha)) == 10,
            "old 2024 PAL SoundTrigger source inventory drift")
    for token in (
        "BOARD_SUPPORTS_OPENSOURCE_STHAL",
        "TARGET_USES_QCOM_MM_AUDIO", "TARGET_USES_QCOM_AUDIO_AR",
        "LOCAL_MODULE               := sound_trigger.primary.$(TARGET_BOARD_PLATFORM)",
        "SoundTriggerDevice.cpp", "SoundTriggerSession.cpp",
        "libar-pal", "libhidlbase",
        "LSM_HIDL_ENABLED",
    ):
        require(token in make, "old PAL STHAL make graph changed: " + token)
    for token in (
        "struct sound_trigger_hw_device",
        "sthal_prop_api_version",
        "stdev_load_sound_model(",
        "stdev_start_recognition(",
        "dlsym(ahal_handle_,",
    ):
        require(token in device,
                "old PAL-backed legacy SoundTrigger device/API changed: " + token)
    require('"PalApi.h"' in device
            and "pal_stream_open(" in session
            and "pal_stream_close(" in session,
            "PAL-backed old recognition pipeline changed")
    require("AServiceManager_addService(" not in device,
            "old PAL SoundTrigger now registers Binder; revise decision")
    print("PASS: pinned 2024 PAL STHAL still uses legacy sound_trigger_hw_device")
    print("PASS: old PAL hooks to audio callback ABI and optional LSM HIDL")
    print("DECISION: no 2024 sound_trigger.primary.* in Android17 active source")


def archived_c(root):
    sha = pin(root, "refs/remotes/origin/seventeen",
              OLD_GCS_SHA, OLD_GCS_TREE, "2023 C/GCS STHAL")
    make = show(root, sha, "Android.mk")
    require("ifneq ($(TARGET_USES_QCOM_AUDIO_AR),true)" in make
            and "st_hw_session_gcs.c" in make
            and "st_hw_session_lsm.c" in make,
            "older C/GCS sound trigger complement changed")
    print("PASS: old 2023 C STHAL incompatible with enabling PAL AudioReach")


def newer_date_not_newer_interface(root):
    sha = pin(root, "refs/remotes/origin/calcite-8650",
              AOSPA_SHA, AOSPA_TREE, "2026 AOSPA Soong legacy PAL ST")
    bp = show(root, sha, "Android.bp")
    device = show(root, sha, "SoundTriggerDevice.cpp")
    require(len(paths(root, sha)) == 10,
            "AOSPA Sep2026 PAL STHAL source count changed")
    for token in (
        "target_board_platform_cc_library_shared",
        'name: "sound_trigger.primary.%s"',
        '"SoundTriggerDevice.cpp"', '"SoundTriggerSession.cpp"',
        ":libar-pal", '"libhidlbase"',
    ):
        require(token in bp,
                "newly dated AOSPA legacy ST module changed: " + token)
    require("struct sound_trigger_hw_device" in device
            and "AServiceManager_addService(" not in device,
            "AOSPA legacy PAL ST now exposes AIDL; re-evaluate status")
    print("PASS: Sept2026 AOSPA calcite-8650 ST remains a legacy PAL HAL")
    print("DECISION: newer patch date alone is not a SoundTrigger3 AIDL port")


def aosp17_contract(root):
    sha = pin(root, "refs/remotes/origin/port/a17-hardware-interfaces-pe-20261103",
              IFACE_SHA, IFACE_TREE, "PE selected Android17 interfaces")
    bp = show(root, sha, "soundtrigger/aidl/Android.bp")
    require('name: "android.hardware.soundtrigger3"' in bp
            and 'stability: "vintf"' in bp
            and "frozen: true" in bp,
            "PE AOSP17 stable SoundTrigger HAL source changed")
    for ver in ("1", "2", "3", "4"):
        require(f'version: "{ver}"' in bp,
                "AOSP17 SoundTrigger3 version missing: " + ver)
    require('latest_android_hardware_soundtrigger3 = "android.hardware.soundtrigger3-V4"'
            in bp,
            "new AOSP17 selected SoundTrigger3 version changed")
    print("PASS: AOSP17 frozen SoundTrigger3 AIDL V1..V4 already selected")


def actual_modern_aidl(st_root, primary_root):
    st = pin(st_root, "refs/remotes/origin/aosp/AUDIO.LA.10.0.r1",
             MODERN_SHA, MODERN_TREE, "Sony-hosted Qualcomm modern AIDL ST")
    primary = pin(primary_root,
                  "refs/remotes/origin/aosp/AUDIO.LA.10.0.r1",
                  PRIMARY_SHA, PRIMARY_TREE,
                  "Sony-hosted Qualcomm Android17 primary HAL")
    make = show(st_root, st, "Android.mk")
    service = show(st_root, st, "src/soundtriggerhw/Service.cpp")
    vintf = ET.fromstring(show(st_root, st, "configs/soundtrigger.qti.xml"))
    assert_ = (
        "LOCAL_MODULE               := libsoundtriggerhal.qti",
        "android.hardware.soundtrigger3-V1-ndk",
        "libar-pal",
        "src/soundtriggerhw/Service.cpp",
    )
    require(all(x in make for x in assert_),
            "modern Qualcomm source not a PAL-backed AIDL NDK factory")
    require("createISoundTriggerFactory()" in service
            and "AServiceManager_addService(" in service
            and 'SoundTriggerHw::descriptor + "/default"' in service,
            "modern Qualcomm AIDL SoundTrigger registration changed")
    declarations = {
        (x.findtext("name"), x.findtext("version"), x.findtext("fqname"),
         x.get("format"))
        for x in vintf.findall("hal")
    }
    require(declarations == {
        ("android.hardware.soundtrigger3", "1",
         "ISoundTriggerHw/default", "aidl"),
    }, "modern vendor AIDL1 VINTF differs from AOSP17 frozen V4")
    top=show(primary_root, primary, "Android.mk")
    svc=show(primary_root, primary, "hal/service/Service.cpp")
    require("android.hardware.audio.core-V3-ndk" in top
            and "android.hardware.audio.effect-V4-ndk" in top
            and "parseInterfaces()" in svc
            and "dlopen(libraryName.c_str()" in svc,
            "modern Qualcomm Android17 primary AIDL/service loader changed")
    print("PASS: genuine Qualcomm-derived AIDL V1 factory and Android17 audio core V3")
    print("WARN: AIDL V1 implementation != AOSP17 frozen V4 and requires factory config")


def manifest(root):
    root=Path(root)
    entry=ET.parse(root / "default.xml").getroot()
    require(len(entry) == 1 and entry[0].tag == "include"
            and entry[0].get("name") == "aosp17_pe_p2_kernel_configs.xml",
            "AOSP17 default switched to unbuilt Qualcomm preview")
    preview=ET.parse(
        root / "aosp17_pe_p2_qcom_audio_aidl_candidate.xml").getroot()
    projects=preview.findall("project")
    old_path=[p for p in projects if p.get("path")==OLD_PATH]
    require(len(projects)==6 and len(old_path)==1
            and old_path[0].attrib=={
                "path": OLD_PATH,
                "name": "vendor-qcom-opensource-audio-hal-st-hal-ar",
                "remote": "sony-qcom-audio-review",
                "revision": MODERN_SHA,
                "upstream": "refs/heads/aosp/AUDIO.LA.10.0.r1",
                "groups": "device",
            }, "modern ST source owner not pinned correctly in preview")
    validator=(root / "tools/validate_aosp17_base_profiles.py").read_text()
    tests=(root / "tools/test_aosp17_manifest_entrypoint.py").read_text()
    require(f'if "{OLD_PATH}" in projects:' in validator
            and f'"{OLD_REPO}"' in validator,
            "row177 legacy PAL source manifest blocker missing")
    for method in (
        "test_old_qualcomm_pal_sthal_ar_not_enabled_in_android17",
        "test_new_qualcomm_aidl_candidate_cannot_use_old_pal_hal_owner",
    ):
        require(f"def {method}(" in tests,
                "row177 negative test missing: " + method)
    subprocess.run(
        [sys.executable, str(root/"tools/validate_aosp17_base_profiles.py")],
        cwd=root, check=True)
    print("PASS: 25 AOSP17 source stages and 6 modern candidate pins protected")
    print("PASS: old PAL source excluded, active default unchanged")


def main():
    require(len(sys.argv)==8,
            "usage: OLD_AR OLD_GCS AOSPA_2026 MODERN_AIDL MODERN_PRIMARY"
            " PE_AOSP17_INTERFACE PE_MANIFEST")
    roots=[Path(arg).resolve() for arg in sys.argv[1:]]
    require(all(p.is_dir() for p in roots), "one or more source checkout missing")
    archived_pe_pal(roots[0])
    archived_c(roots[1])
    newer_date_not_newer_interface(roots[2])
    actual_modern_aidl(roots[3], roots[4])
    aosp17_contract(roots[5])
    manifest(roots[6])
    print("PASS: row177 old PAL SoundTrigger excluded; newer AIDL preview retained")
    print("NOT TESTED: whole Android17 Qualcomm Soong/AIDL, ADSP, VINTF, SELinux,")
    print("mic/hotword, audio routes, CTS/VTS, actual mondrian hardware/firmware")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError, ET.ParseError,
            subprocess.CalledProcessError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
