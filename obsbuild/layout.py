"""Pure layout spec for the Stream Kit collection. No OBS imports; unit-tested."""
from __future__ import annotations

from dataclasses import dataclass

W, H = 1920, 1080
MARGIN = 48
GAP = 16

# Source names. Move transition animates items whose names match across scenes: never rename one in isolation.
LIBRARY = "[SRC] Library"
CAM = "[SRC] Cam"
AUDIO = "[SRC] Audio"   # desktop/game audio only
MIC = "[SRC] Mic"
MUSIC = "[SRC] Music"
GAME = "Game"
CONTENT = "Content"
CHAT = "Chat"
ALERTS = "Alerts"
BRAND = "Brand Chip"
GAME_BLUR = "Game Blur"
SCREEN = {m: f"Screen {m.capitalize()}" for m in ("starting", "brb", "ending", "privacy", "bg")}

SOURCE_SCENES = (LIBRARY, CAM, AUDIO, MIC, MUSIC)
MAIN_SCENES = ("Starting Soon", "Gaming", "Just Chatting", "React", "BRB", "Ending", "Privacy")

# Where the StreamElements AlertBox widget must sit inside its 1920x1080 SE overlay (x, y, w, h).
ALERT_ZONE = (560, 48, 800, 300)


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def intersects(self, o: "Box") -> bool:
        return not (self.right <= o.x or o.right <= self.x or self.bottom <= o.y or o.bottom <= self.y)

    def inside_canvas(self) -> bool:
        return self.x >= 0 and self.y >= 0 and self.right <= W and self.bottom <= H


ALIGN_CENTER = 0
ALIGN_BOTTOM_LEFT = 9   # OBS_ALIGN_LEFT (1) | OBS_ALIGN_BOTTOM (8): chat grows upward from the bottom edge


@dataclass(frozen=True)
class Item:
    source: str
    box: Box
    visible: bool = True
    align: int = ALIGN_CENTER   # where the source sits inside its box when aspect ratios differ


FULL = Box(0, 0, W, H)
SIDE_CHAT = Box(W - MARGIN - 448, 200, 448, 680)


def _gaming() -> tuple[Item, ...]:
    cam = Box(MARGIN, H - MARGIN - 225, 400, 225)
    brand = Box(MARGIN, cam.y - GAP - 44, 400, 44)
    chat = Box(W - MARGIN - 420, H - MARGIN - 620, 420, 620)
    return (Item(GAME, FULL), Item(CAM, cam), Item(BRAND, brand), Item(CHAT, chat, visible=False, align=ALIGN_BOTTOM_LEFT))


def _just_chatting() -> tuple[Item, ...]:
    cam = Box(MARGIN, 180, 1280, 720)
    chat_x = cam.right + MARGIN
    chat = Box(chat_x, 180, W - MARGIN - chat_x, 720)
    brand = Box(MARGIN, cam.bottom + GAP, 400, 44)
    return (Item(SCREEN["bg"], FULL), Item(CAM, cam), Item(CHAT, chat, align=ALIGN_BOTTOM_LEFT), Item(BRAND, brand))


def _react() -> tuple[Item, ...]:
    content = Box(MARGIN, MARGIN, 1376, 774)
    side_x = content.right + MARGIN
    cam = Box(side_x, MARGIN, W - MARGIN - side_x, 225)
    chat = Box(side_x, cam.bottom + GAP, cam.w, H - MARGIN - (cam.bottom + GAP))
    brand = Box(MARGIN, content.bottom + GAP, 400, 44)
    return (Item(SCREEN["bg"], FULL), Item(CONTENT, content), Item(CAM, cam), Item(CHAT, chat, align=ALIGN_BOTTOM_LEFT), Item(BRAND, brand))


def _holding(mode: str) -> tuple[Item, ...]:
    return (Item(SCREEN[mode], FULL), Item(CHAT, SIDE_CHAT, align=ALIGN_BOTTOM_LEFT))


def scenes() -> dict[str, tuple[Item, ...]]:
    """Main scenes, items ordered bottom -> top.

    Audio routing is by presence: Mic is left out of BRB/Privacy (hard mute), desktop audio
    only plays in live scenes so setup noise / Discord never leaks on holding screens."""
    alerts, mic, desktop, music = Item(ALERTS, FULL), Item(MIC, FULL), Item(AUDIO, FULL), Item(MUSIC, FULL)
    live = (alerts, desktop, mic)
    return {
        "Starting Soon": (*_holding("starting"), music, alerts, mic),
        "Gaming": (*_gaming(), *live),
        "Just Chatting": (*_just_chatting(), *live),
        "React": (*_react(), *live),
        "BRB": (Item(GAME_BLUR, FULL), *_holding("brb"), music, alerts),
        "Ending": (*_holding("ending"), music, alerts, mic),
        "Privacy": (Item(SCREEN["privacy"], FULL), music),
    }
