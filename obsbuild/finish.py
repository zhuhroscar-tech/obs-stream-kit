"""Things obs-websocket cannot do: add the Move transition and bind hotkeys.

These live in OBS's own files, so they are edited while OBS is closed:
  basic/scenes/Stream_Kit.json      transitions + per-source hotkeys
  basic/profiles/Stream_Kit/basic.ini  [Hotkeys] frontend hotkeys (save replay)
Modifiers on macOS: control = ⌃, alt = ⌥, shift = ⇧, command = ⌘.
"""
from __future__ import annotations

import json
import re

from . import layout as L

TRANSITION = {"name": "Move", "id": "move_transition", "settings": {}}
TRANSITION_MS = 450

SCENE_KEYS = {"Starting Soon": "1", "Gaming": "2", "Just Chatting": "3", "React": "4",
              "BRB": "5", "Ending": "6", "Privacy": "0"}


def bind(key: str, shift: bool = False) -> list[dict]:
    b: dict = {"control": True, "alt": True}
    if shift:
        b["shift"] = True
    b["key"] = f"OBS_KEY_{key}"
    return [b]


def finish_collection(d: dict) -> dict:
    if not any(t.get("id") == TRANSITION["id"] for t in d.get("transitions", [])):
        d.setdefault("transitions", []).append(dict(TRANSITION))
    d["current_transition"] = TRANSITION["name"]
    d["transition_duration"] = TRANSITION_MS
    for src in d["sources"]:
        hk = src.setdefault("hotkeys", {})
        if src["id"] == "scene" and src["name"] in SCENE_KEYS:
            hk["OBSBasic.SelectScene"] = bind(SCENE_KEYS[src["name"]])
        if src["id"] == "scene" and src["name"] == "Gaming":
            for item in src["settings"]["items"]:
                if item["name"] == L.CHAT:
                    hk[f"libobs.show_scene_item.{item['id']}"] = bind("C")
                    hk[f"libobs.hide_scene_item.{item['id']}"] = bind("C", shift=True)
        if src["name"] == "Mic":
            hk["libobs.mute"] = bind("M")
            hk["libobs.unmute"] = bind("M", shift=True)
    return d


def finish_profile_ini(text: str) -> str:
    """Bind ⌃⌥S to "save replay" in [Hotkeys], preserving every other line verbatim.

    OBS ≤ 32.2 reads `ReplayBuffer={"ReplayBuffer.Save":[...]}`; newer builds read
    `OBSBasic.SaveReplayBuffer={"bindings":[...]}` (and migrate the legacy key). Write both."""
    lines = [
        "ReplayBuffer=" + json.dumps({"ReplayBuffer.Save": bind("S")}, separators=(",", ":")),
        "OBSBasic.SaveReplayBuffer=" + json.dumps({"bindings": bind("S")}, separators=(",", ":")),
    ]
    text = re.sub(r"(?m)^(ReplayBuffer|OBSBasic\.SaveReplayBuffer)=.*\n?", "", text)
    block = "\n".join(lines) + "\n"
    if re.search(r"(?m)^\[Hotkeys\]\s*$", text):
        return re.sub(r"(?m)^\[Hotkeys\]\s*\n", lambda m: "[Hotkeys]\n" + block, text, count=1)
    return text.rstrip("\n") + "\n\n[Hotkeys]\n" + block
