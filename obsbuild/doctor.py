"""Read-only health checks. Prints one line per check with a single glyph system: ✓ pass, ✗ fail."""
from __future__ import annotations

from . import layout as L
from .build import VIDEO
from .specs import COMPOSITE_BLUR_KIND, MOVE_TRANSITION_KIND, SOURCE_CLONE_KIND


def doctor_checks(c) -> list[tuple[bool, str]]:
    out: list[tuple[bool, str]] = []
    major = int(c.call("GetVersion")["obsVersion"].split(".")[0])
    out.append((major >= 32, f"OBS major version {major} (need ≥ 32)"))
    kinds = (("transition", "GetTransitionKindList", "transitionKinds", MOVE_TRANSITION_KIND),
             ("input", "GetInputKindList", "inputKinds", SOURCE_CLONE_KIND),
             ("filter", "GetSourceFilterKindList", "sourceFilterKinds", COMPOSITE_BLUR_KIND))
    for label, req, key, kind in kinds:
        present = kind in c.call(req)[key]
        out.append((present, f"{label} kind {kind} {'loaded' if present else 'missing — plugin not installed'}"))
    t = c.call("GetCurrentSceneTransition")
    ok = t.get("transitionKind") == MOVE_TRANSITION_KIND
    out.append((ok, f"current transition {t.get('transitionName')} "
                    f"{t.get('transitionDuration')} ms" + ("" if ok else " (want Move — run finish)")))
    special = c.call("GetSpecialInputs")
    for slot in ("desktop1", "desktop2", "mic1", "mic2", "mic3", "mic4"):
        name = special.get(slot)
        out.append((name is None, f"global audio {slot} disabled" if name is None
                    else f"global audio {slot} = {name} (Mic/Aux duplicate — disable in Settings → Audio)"))
    video = c.call("GetVideoSettings")
    for k, v in VIDEO.items():
        out.append((video.get(k) == v, f"video {k} = {video.get(k)} (want {v})"))
    scenes = {s["sceneName"] for s in c.call("GetSceneList")["scenes"]}
    for s in L.MAIN_SCENES:
        out.append((s in scenes, f"scene {s} {'present' if s in scenes else 'missing'}"))
    return out


def print_report(checks) -> int:
    for ok, msg in checks:
        print(f"{'✓' if ok else '✗'} {msg}")
    failed = sum(1 for ok, _ in checks if not ok)
    print(f"\n{len(checks) - failed}/{len(checks)} checks passed")
    return 1 if failed else 0
