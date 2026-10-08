"""Generate overlays/config.js and per-mode screen HTML from config/kit.json."""
from __future__ import annotations

import json
from pathlib import Path

PUBLIC_KEYS = ("twitch_login", "display_name", "socials", "starting_minutes")
MODES = ("starting", "brb", "ending", "privacy", "bg")


def config_js(kit: dict) -> str:
    public = {k: kit[k] for k in PUBLIC_KEYS if k in kit}
    return "window.KIT = " + json.dumps(public, ensure_ascii=False) + ";\n"


def screen_html(template: str, mode: str) -> str:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    if template.count("<body>") != 1:
        raise ValueError("template must contain exactly one literal <body>")
    return template.replace("<body>", f'<body data-mode="{mode}">', 1)


def render(kit: dict, root: Path) -> list[Path]:
    ov = root / "overlays"
    cfg = ov / "config.js"
    cfg.write_text(config_js(kit), encoding="utf-8")
    template = (ov / "screen.template.html").read_text(encoding="utf-8")
    paths = [cfg]
    for mode in MODES:
        p = ov / f"screen-{mode}.html"
        p.write_text(screen_html(template, mode), encoding="utf-8")
        paths.append(p)
    return paths
