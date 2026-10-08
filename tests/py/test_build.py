from obsbuild import layout as L
from obsbuild.build import PROFILE_PARAMS, apply_all, configure_output


def kit(tmp_path):
    return {"twitch_login": "x", "display_name": "X", "socials": ["a"], "starting_minutes": 5,
            "chat_url": "https://chat", "streamelements_alertbox_url": "https://se",
            "cam_device_name": "oscar Camera", "mic_device_name": "oscar Microphone",
            "music_file": str(tmp_path / "m.mp3")}


def test_apply_all_builds_every_scene_with_expected_items(fake, tmp_path):
    apply_all(fake, kit(tmp_path), tmp_path)
    for s in L.MAIN_SCENES + L.SOURCE_SCENES:
        assert s in fake.scenes
    assert set(fake.scenes["Gaming"]) >= {L.GAME, L.CAM, L.BRAND, L.CHAT, L.ALERTS, L.AUDIO, L.MIC}
    assert set(fake.scenes[L.MIC]) == {"Mic"}
    assert set(fake.scenes[L.AUDIO]) == {"Desktop Audio"}
    assert fake.inputs["Camera"][1]["device"] == "UUID-1"
    assert fake.inputs["Mic"][1]["device_id"] == "MIC-1"
    assert fake.filters["Desktop Audio"]["Duck Under Voice"][1]["sidechain_source"] == "Mic"


def test_apply_all_is_idempotent(fake, tmp_path):
    apply_all(fake, kit(tmp_path), tmp_path)
    n = len(fake.calls)
    log = apply_all(fake, kit(tmp_path), tmp_path)
    assert log == []
    assert [c for c, _ in fake.calls[n:] if c.startswith("Create")] == []


def test_chat_url_defaults_to_jchat_for_the_twitch_login(fake, tmp_path):
    k = kit(tmp_path)
    del k["chat_url"]
    k["twitch_login"] = "oscar"
    apply_all(fake, k, tmp_path)
    url = fake.inputs[L.CHAT][1]["url"]
    assert url.startswith("https://www.giambaj.it/twitch/jchat/v2/?channel=oscar&")
    assert "hide_commands=true" in url and "fade=30" in url


def test_local_overlays_disable_obs_default_transparent_body_css(fake, tmp_path):
    apply_all(fake, kit(tmp_path), tmp_path)
    for name, (kind, settings) in fake.inputs.items():
        if kind == "browser_source" and settings.get("is_local_file"):
            assert settings["css"] == "", name


def test_configure_output_sets_video_and_every_profile_param(fake):
    configure_output(fake)
    assert [c for c, _ in fake.calls].count("SetProfileParameter") == len(PROFILE_PARAMS)
    video = next(d for c, d in fake.calls if c == "SetVideoSettings")
    assert (video["outputWidth"], video["outputHeight"], video["fpsNumerator"]) == (1280, 720, 60)
