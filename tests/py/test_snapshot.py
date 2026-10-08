import base64

import pytest
from obsbuild.snapshot import snapshot_all

PNG = "data:image/png;base64," + base64.b64encode(b"\x89PNG fake").decode()


class ShotObs:
    def __init__(self, streaming=False):
        self.streaming = streaming
        self.program = "Gaming"
        self.shots = []

    def call(self, req, data=None):
        if req == "GetStreamStatus":
            return {"outputActive": self.streaming}
        if req == "GetCurrentProgramScene":
            return {"currentProgramSceneName": self.program}
        if req == "SetCurrentProgramScene":
            self.program = data["sceneName"]
        if req == "GetSourceScreenshot":
            self.shots.append((data["sourceName"], self.program))
            return {"imageData": PNG}
        return {}


def test_each_scene_is_live_when_captured_and_original_restored(tmp_path):
    obs = ShotObs()
    paths = snapshot_all(obs, tmp_path, ["Starting Soon", "BRB"], sleep=lambda s: None)
    assert obs.shots == [("Starting Soon", "Starting Soon"), ("BRB", "BRB")]
    assert obs.program == "Gaming"
    assert [p.name for p in paths] == ["Starting_Soon.png", "BRB.png"]
    assert paths[0].read_bytes() == b"\x89PNG fake"


def test_refuses_while_streaming(tmp_path):
    with pytest.raises(RuntimeError):
        snapshot_all(ShotObs(streaming=True), tmp_path, ["BRB"], sleep=lambda s: None)
