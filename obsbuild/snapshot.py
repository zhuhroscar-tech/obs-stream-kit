from __future__ import annotations

import base64
from pathlib import Path


def snapshot_all(client, out_dir: Path, scenes) -> list[Path]:
    """Render each scene to PNG through OBS (does not change the live program scene)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for scene in scenes:
        r = client.call("GetSourceScreenshot", {"sourceName": scene, "imageFormat": "png", "imageWidth": 960})
        p = out_dir / f"{scene.replace(' ', '_')}.png"
        p.write_bytes(base64.b64decode(r["imageData"].split(",", 1)[1]))
        paths.append(p)
    return paths
