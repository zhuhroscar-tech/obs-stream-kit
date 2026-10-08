"""Orchestrates a full, idempotent build of the Stream Kit collection."""
from __future__ import annotations

from pathlib import Path

from . import layout as L
from .applier import Applier
from .specs import filter_specs, input_specs

COLLECTION = "Stream Kit"
PROFILE = "Stream Kit"

VIDEO = {"fpsNumerator": 60, "fpsDenominator": 1, "baseWidth": 1920, "baseHeight": 1080,
         "outputWidth": 1280, "outputHeight": 720}

PROFILE_PARAMS = [
    ("Video", "ScaleType", "lanczos"),
    ("Output", "Mode", "Simple"),
    ("SimpleOutput", "StreamEncoder", "apple_h264"),
    ("SimpleOutput", "VBitrate", "6000"),
    ("SimpleOutput", "ABitrate", "160"),
    ("SimpleOutput", "RecQuality", "Stream"),      # reuse the stream encode: no second encoder on a fanless Mac
    ("SimpleOutput", "RecFormat2", "hybrid_mp4"),
    ("SimpleOutput", "RecRB", "true"),             # replay buffer for clips
    ("SimpleOutput", "RecRBTime", "60"),
]


def configure_output(client) -> None:
    client.call("SetVideoSettings", dict(VIDEO))
    for category, name, value in PROFILE_PARAMS:
        client.call("SetProfileParameter", {"parameterCategory": category, "parameterName": name,
                                            "parameterValue": value})


def apply_all(client, kit: dict, root: Path) -> list[str]:
    a = Applier(client)
    for scene in L.SOURCE_SCENES + L.MAIN_SCENES:
        a.ensure_scene(scene)
    for scene, name, kind, settings in input_specs(kit, root):
        a.ensure_input(scene, name, kind, settings)
    a.select_device("Camera", "device", kit["cam_device_name"])
    a.select_device("Mic", "device_id", kit["mic_device_name"])
    a.build_scene(L.CAM, (L.Item("Camera", L.FULL),), prune=True)
    a.build_scene(L.MIC, (L.Item("Mic", L.FULL),), prune=True)
    a.build_scene(L.AUDIO, (L.Item("Desktop Audio", L.FULL),), prune=True)
    a.build_scene(L.MUSIC, (L.Item("Music", L.FULL),), prune=True)
    for source, name, kind, settings in filter_specs(root):
        a.ensure_filter(source, name, kind, settings)
    client.call("SetInputVolume", {"inputName": "Music", "inputVolumeDb": -20.0})
    for scene, items in L.scenes().items():
        a.build_scene(scene, items, prune=True)   # the kit owns these scenes; stale items are removed
    # The panic button must be instant.
    client.call("SetSceneSceneTransitionOverride",
                {"sceneName": "Privacy", "transitionName": "Cut", "transitionDuration": 50})
    return a.log
