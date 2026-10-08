"""Usage: .venv/bin/python -m obsbuild {render|probe|apply|finish|doctor|snapshot|check-audio|check-hotkeys}"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_kit() -> dict:
    p = ROOT / "config" / "kit.json"
    if not p.exists():
        sys.exit("✗ config/kit.json missing — copy config/kit.example.json and fill it in")
    return json.loads(p.read_text(encoding="utf-8"))


def client():
    from .obsclient import ObsClient
    pw = subprocess.run(["security", "find-generic-password", "-s", "obs-websocket", "-a", "obs", "-w"],
                        capture_output=True, text=True)
    if pw.returncode != 0:
        sys.exit("✗ no Keychain item 'obs-websocket' — run: security add-generic-password -s obs-websocket -a obs -w")
    return ObsClient("localhost", 4455, pw.stdout.strip())


def render_files(kit: dict) -> None:
    from .mask import write_mask
    from .render import render
    for p in render(kit, ROOT):
        print(f"✓ wrote {p.relative_to(ROOT)}")
    print(f"✓ wrote {write_mask(ROOT / 'assets' / 'cam-mask.png').relative_to(ROOT)}")


def probe(c) -> None:
    from .specs import COMPOSITE_BLUR_KIND, SOURCE_CLONE_KIND
    print("obs", c.call("GetVersion")["obsVersion"])
    print("transitions", sorted(c.call("GetTransitionKindList")["transitionKinds"]))
    print("inputs", sorted(c.call("GetInputKindList")["inputKinds"]))
    print("filters", sorted(c.call("GetSourceFilterKindList")["sourceFilterKinds"]))
    for req, key, kind in (("GetSourceFilterDefaultSettings", "filterKind", COMPOSITE_BLUR_KIND),
                           ("GetInputDefaultSettings", "inputKind", SOURCE_CLONE_KIND)):
        try:
            print(kind, "defaults", json.dumps(c.call(req, {key: kind})))
        except Exception as e:  # noqa: BLE001 — probe must keep going and report
            print(kind, "defaults unavailable:", e)


def check_audio(c) -> int:
    """Mic/desktop audio are routed by scene membership; verify against OBS's live 'active' state."""
    from . import layout as L
    fails = 0
    original = c.call("GetCurrentProgramScene")["currentProgramSceneName"]
    try:
        for scene, items in L.scenes().items():
            c.call("SetCurrentProgramScene", {"sceneName": scene})
            time.sleep(1.0)
            names = [i.source for i in items]
            for src, item in (("Mic", L.MIC), ("Desktop Audio", L.AUDIO)):
                want = item in names
                got = c.call("GetSourceActive", {"sourceName": src})["videoActive"]
                ok = got == want
                fails += not ok
                print(f"{'✓' if ok else '✗'} {scene:<14} {src:<14} live={got} (want {want})")
    finally:
        c.call("SetCurrentProgramScene", {"sceneName": original})
    return 1 if fails else 0


def finish_files() -> int:
    """Edit OBS's own files for what obs-websocket cannot do. OBS must be closed."""
    import shutil
    from .build import COLLECTION, PROFILE
    from .finish import finish_collection, finish_profile_ini
    if subprocess.run(["pgrep", "-x", "OBS"], capture_output=True).returncode == 0:
        print("✗ quit OBS first (it rewrites these files on exit)")
        return 1
    base = Path.home() / "Library" / "Application Support" / "obs-studio" / "basic"
    coll = base / "scenes" / (COLLECTION.replace(" ", "_") + ".json")
    prof = base / "profiles" / PROFILE.replace(" ", "_") / "basic.ini"
    backups = ROOT / "out" / "backups" / time.strftime("%Y%m%d-%H%M%S")
    backups.mkdir(parents=True, exist_ok=True)
    for f in (coll, prof):
        shutil.copy2(f, backups / f.name)
    coll.write_text(json.dumps(finish_collection(json.loads(coll.read_text(encoding="utf-8"))), indent=4),
                    encoding="utf-8")
    prof.write_text(finish_profile_ini(prof.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"✓ Move transition + hotkeys written (backup: {backups.relative_to(ROOT)})")
    return 0


def check_hotkeys(c) -> int:
    """Inject each scene hotkey into OBS and confirm the program scene follows."""
    from .finish import SCENE_KEYS
    fails = 0
    original = c.call("GetCurrentProgramScene")["currentProgramSceneName"]
    try:
        for scene, key in SCENE_KEYS.items():
            c.call("TriggerHotkeyByKeySequence", {"keyId": f"OBS_KEY_{key}",
                                                  "keyModifiers": {"control": True, "alt": True}})
            time.sleep(1.0)
            got = c.call("GetCurrentProgramScene")["currentProgramSceneName"]
            ok = got == scene
            fails += not ok
            print(f"{'✓' if ok else '✗'} ⌃⌥{key} → {got} (want {scene})")

        def press(key, shift=False):
            mods = {"control": True, "alt": True, **({"shift": True} if shift else {})}
            c.call("TriggerHotkeyByKeySequence", {"keyId": f"OBS_KEY_{key}", "keyModifiers": mods})
            time.sleep(0.5)

        chat_id = c.call("GetSceneItemId", {"sceneName": "Gaming", "sourceName": "Chat"})["sceneItemId"]
        checks = (
            ("⌃⌥M mute mic", lambda: press("M"),
             lambda: c.call("GetInputMute", {"inputName": "Mic"})["inputMuted"] is True),
            ("⌃⌥⇧M unmute mic", lambda: press("M", True),
             lambda: c.call("GetInputMute", {"inputName": "Mic"})["inputMuted"] is False),
            ("⌃⌥C show chat in Gaming", lambda: press("C"),
             lambda: c.call("GetSceneItemEnabled", {"sceneName": "Gaming", "sceneItemId": chat_id})["sceneItemEnabled"]),
            ("⌃⌥⇧C hide chat in Gaming", lambda: press("C", True),
             lambda: not c.call("GetSceneItemEnabled", {"sceneName": "Gaming", "sceneItemId": chat_id})["sceneItemEnabled"]),
        )
        for label, act, verify in checks:
            act()
            ok = bool(verify())
            fails += not ok
            print(f"{'✓' if ok else '✗'} {label}")
    finally:
        c.call("SetCurrentProgramScene", {"sceneName": original})
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="obsbuild")
    ap.add_argument("command", choices=["render", "probe", "apply", "finish", "doctor", "snapshot",
                                        "check-audio", "check-hotkeys"])
    cmd = ap.parse_args(argv).command
    if cmd == "render":
        render_files(load_kit())
        return 0
    if cmd == "finish":
        return finish_files()
    c = client()
    if cmd == "check-hotkeys":
        return check_hotkeys(c)
    if cmd == "probe":
        probe(c)
        return 0
    if cmd == "apply":
        from .applier import Applier
        from .build import COLLECTION, PROFILE, apply_all, configure_output
        kit = load_kit()
        render_files(kit)
        a = Applier(c)
        a.ensure_collection(COLLECTION)
        time.sleep(2)
        a.ensure_profile(PROFILE)
        time.sleep(2)
        configure_output(c)
        for line in a.log + apply_all(c, kit, ROOT):
            print(line)
        print("✓ apply done")
        return 0
    if cmd == "doctor":
        from .doctor import doctor_checks, print_report
        return print_report(doctor_checks(c))
    if cmd == "snapshot":
        from . import layout as L
        from .snapshot import snapshot_all
        for p in snapshot_all(c, ROOT / "out" / "snapshots", L.MAIN_SCENES):
            print(f"✓ {p.relative_to(ROOT)}")
        return 0
    return check_audio(c)


if __name__ == "__main__":
    sys.exit(main())
