import json

from obsbuild import finish as F


def collection():
    return {
        "transitions": [],
        "current_transition": "Fade",
        "transition_duration": 300,
        "sources": [
            {"id": "scene", "name": n, "hotkeys": {"OBSBasic.SelectScene": []},
             "settings": {"items": [{"name": "Chat", "id": 7}] if n == "Gaming" else []}}
            for n in F.SCENE_KEYS
        ] + [{"id": "coreaudio_input_capture", "name": "Mic", "hotkeys": {}}],
    }


def test_adds_move_transition_once_and_makes_it_current():
    d = F.finish_collection(F.finish_collection(collection()))
    assert [t["id"] for t in d["transitions"]] == ["move_transition"]
    assert d["current_transition"] == "Move" and d["transition_duration"] == 450


def test_scene_hotkeys_are_ctrl_alt_digits():
    d = F.finish_collection(collection())
    by_name = {s["name"]: s for s in d["sources"]}
    assert by_name["Gaming"]["hotkeys"]["OBSBasic.SelectScene"] == [{"control": True, "alt": True, "key": "OBS_KEY_2"}]
    assert by_name["Privacy"]["hotkeys"]["OBSBasic.SelectScene"][0]["key"] == "OBS_KEY_0"


def test_chat_toggle_targets_the_chat_item_id_in_gaming():
    hk = {s["name"]: s for s in F.finish_collection(collection())["sources"]}["Gaming"]["hotkeys"]
    assert hk["libobs.show_scene_item.7"] == [{"control": True, "alt": True, "key": "OBS_KEY_C"}]
    assert hk["libobs.hide_scene_item.7"] == [{"control": True, "alt": True, "shift": True, "key": "OBS_KEY_C"}]


def test_mic_mute_and_unmute_hotkeys():
    hk = {s["name"]: s for s in F.finish_collection(collection())["sources"]}["Mic"]["hotkeys"]
    assert hk["libobs.mute"][0]["key"] == "OBS_KEY_M" and "shift" not in hk["libobs.mute"][0]
    assert hk["libobs.unmute"][0]["shift"] is True


def test_profile_hotkeys_set_save_replay_and_keep_other_lines():
    ini = "[General]\nName=Stream Kit\n\n[SimpleOutput]\nRecRB=true\n"
    out = F.finish_profile_ini(ini)
    assert "Name=Stream Kit" in out and "RecRB=true" in out
    line = next(l for l in out.splitlines() if l.startswith("OBSBasic.SaveReplayBuffer="))
    assert json.loads(line.split("=", 1)[1]) == {"bindings": [{"control": True, "alt": True, "key": "OBS_KEY_S"}]}
    legacy = next(l for l in out.splitlines() if l.startswith("ReplayBuffer="))
    assert json.loads(legacy.split("=", 1)[1]) == {"ReplayBuffer.Save": [{"control": True, "alt": True, "key": "OBS_KEY_S"}]}
    assert F.finish_profile_ini(out) == out   # idempotent
