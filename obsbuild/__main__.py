"""Usage: .venv/bin/python -m obsbuild {render|probe|apply|doctor|snapshot|check-macros}"""
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


def check_macros(c) -> int:
    fails = 0
    for scene, want in (("Privacy", True), ("Gaming", False), ("BRB", True), ("Just Chatting", False)):
        c.call("SetCurrentProgramScene", {"sceneName": scene})
        time.sleep(1.5)
        muted = c.call("GetInputMute", {"inputName": "Mic"})["inputMuted"]
        ok = muted == want
        fails += not ok
        print(f"{'✓' if ok else '✗'} {scene:<14} mic muted={muted} (want {want})")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="obsbuild")
    ap.add_argument("command", choices=["render", "probe", "apply", "doctor", "snapshot", "check-macros"])
    cmd = ap.parse_args(argv).command
    if cmd == "render":
        render_files(load_kit())
        return 0
    c = client()
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
    return check_macros(c)


if __name__ == "__main__":
    sys.exit(main())
