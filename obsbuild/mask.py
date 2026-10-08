"""Write a white RGBA PNG whose alpha is a rounded rectangle (for OBS 'Image Mask/Blend' alpha mode)."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


def corner_alpha(x: int, y: int, w: int, h: int, r: int) -> int:
    cx = r - 0.5 if x < r else (w - r - 0.5 if x >= w - r else None)
    cy = r - 0.5 if y < r else (h - r - 0.5 if y >= h - r else None)
    if cx is None or cy is None:
        return 255
    d = math.hypot(x - cx, y - cy)
    return int(round(max(0.0, min(1.0, r - d + 0.5)) * 255))


def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def png_bytes(w: int, h: int, r: int) -> bytes:
    raw = bytearray()
    full_row = b"\x00" + b"\xff" * (w * 4)
    for y in range(h):
        if r <= y < h - r:
            raw += full_row
            continue
        raw.append(0)
        for x in range(w):
            raw += bytes((255, 255, 255, corner_alpha(x, y, w, h, r)))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))


def write_mask(path: Path, w: int = 1920, h: int = 1080, r: int = 58) -> Path:
    """r=58 at 1920 wide ≈ 12 px when the cam is shown 400 px wide (matches chip radius)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png_bytes(w, h, r))
    return path
