"""Every input and filter the kit creates. Plugin kind ids are confirmed by `python -m obsbuild probe`."""
from __future__ import annotations

from pathlib import Path

from . import layout as L

CAMERA_KIND = "macos-avcapture"
SOURCE_CLONE_KIND = "source-clone"
COMPOSITE_BLUR_KIND = "obs_composite_blur"
MOVE_TRANSITION_KIND = "move_transition"

CHAT_CSS = """
body { background: rgba(0,0,0,0) !important; margin: 0; overflow: hidden; }
* { font-family: "Inter", "Inter Variable", -apple-system, sans-serif !important; }
.chat_line { background: rgba(18,20,24,.82); border: 1px solid rgba(255,255,255,.10);
             border-radius: 12px; padding: 8px 12px !important; margin: 0 0 8px !important; color: #F5F6F8; }
"""

DUCK = {"ratio": 4.0, "threshold": -28.0, "attack_time": 10, "release_time": 400,
        "output_gain": 0.0, "sidechain_source": "Mic"}


def _local(path: Path, w: int = 1920, h: int = 1080, fps: int = 30) -> dict:
    return {"is_local_file": True, "local_file": str(path), "width": w, "height": h,
            "fps_custom": True, "fps": fps, "restart_when_active": True, "shutdown": False,
            "reroute_audio": False,
            "css": ""}  # OBS's default CSS forces a transparent <body>, which would erase our backgrounds


def input_specs(kit: dict, root: Path) -> list[tuple[str, str, str, dict]]:
    """(home scene, input name, input kind, settings) in creation order."""
    ov = root / "overlays"
    specs = [
        (L.CAM, "Camera", CAMERA_KIND, {}),
        (L.MIC, "Mic", "coreaudio_input_capture", {}),
        (L.AUDIO, "Desktop Audio", "sck_audio_capture", {}),
        (L.MUSIC, "Music", "ffmpeg_source", {"local_file": str(Path(kit["music_file"]).expanduser()),
                                              "looping": True, "restart_on_activate": False,
                                              "close_when_inactive": False}),
        (L.LIBRARY, L.GAME, "screen_capture", {"type": 1, "show_cursor": False, "hide_obs": True}),
        (L.LIBRARY, L.CONTENT, "screen_capture", {"type": 1, "show_cursor": True, "hide_obs": True}),
        (L.LIBRARY, L.CHAT, "browser_source", {"is_local_file": False, "url": kit["chat_url"],
                                               "width": 448, "height": 720, "fps_custom": True, "fps": 30,
                                               "css": CHAT_CSS, "shutdown": False}),
        (L.LIBRARY, L.ALERTS, "browser_source", {"is_local_file": False, "url": kit["streamelements_alertbox_url"],
                                                 "width": 1920, "height": 1080, "fps_custom": True, "fps": 60,
                                                 "shutdown": False, "reroute_audio": False}),
        (L.LIBRARY, L.BRAND, "browser_source", _local(ov / "brandbar.html", 400, 44)),
        (L.LIBRARY, L.GAME_BLUR, SOURCE_CLONE_KIND, {"clone": L.GAME}),
    ]
    for mode, name in L.SCREEN.items():
        specs.append((L.LIBRARY, name, "browser_source", _local(ov / f"screen-{mode}.html")))
    return specs


def filter_specs(root: Path) -> list[tuple[str, str, str, dict]]:
    """(source, filter name, filter kind, settings) in chain order."""
    return [
        ("Camera", "Color", "color_filter_v2", {"contrast": 0.05, "saturation": 0.10}),
        ("Camera", "Sharpen", "sharpness_filter_v2", {"sharpness": 0.08}),
        ("Camera", "Rounded Mask", "mask_filter_v2",
         {"type": "mask_alpha_filter.effect", "image_path": str(root / "assets" / "cam-mask.png")}),
        ("Mic", "Noise Suppression", "noise_suppress_filter_v2", {"method": "rnnoise"}),
        ("Mic", "Gain", "gain_filter", {"db": 4.0}),
        ("Mic", "Compressor", "compressor_filter",
         {"ratio": 4.0, "threshold": -18.0, "attack_time": 6, "release_time": 60, "output_gain": 0.0}),
        ("Mic", "Limiter", "limiter_filter", {"threshold": -3.0, "release_time": 60}),
        ("Desktop Audio", "Duck Under Voice", "compressor_filter", DUCK),
        ("Music", "Duck Under Voice", "compressor_filter", DUCK),
        (L.GAME_BLUR, "Blur", COMPOSITE_BLUR_KIND, {"radius": 40.0}),
    ]
