from __future__ import annotations

import base64
import time
from pathlib import Path


def snapshot_all(client, out_dir: Path, scenes, settle: float = 2.0, sleep=time.sleep) -> list[Path]:
    """Render each scene to PNG. Sources only render while shown, so each scene is made the
    program scene briefly; the original scene is restored. Refuses while streaming."""
    if client.call("GetStreamStatus").get("outputActive"):
        raise RuntimeError("refusing to cycle scenes while streaming")
    original = client.call("GetCurrentProgramScene").get("currentProgramSceneName")
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    try:
        for scene in scenes:
            client.call("SetCurrentProgramScene", {"sceneName": scene})
            sleep(settle)
            r = client.call("GetSourceScreenshot", {"sourceName": scene, "imageFormat": "png", "imageWidth": 960})
            p = out_dir / f"{scene.replace(' ', '_')}.png"
            p.write_bytes(base64.b64decode(r["imageData"].split(",", 1)[1]))
            paths.append(p)
    finally:
        if original:
            client.call("SetCurrentProgramScene", {"sceneName": original})
    return paths
