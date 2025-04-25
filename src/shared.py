from __future__ import annotations

import typing as t

import pygame
import pytmx

if t.TYPE_CHECKING:
    from src.enums import State
    from src.player import Player
    from src.utils import Camera

# Const
TILE_SIDE = 16
WORLD_GRAVITY = 100
MAX_FALL_VELOCITY = 300
PALETTE: dict[t.Literal["purple", "grey", "black", "yellow"], str] = {
    "black": "#202020",
    "grey": "#393939",
    "purple": "#725956",
    "yellow": "#f6cd26",
}
ENTITY_CLASS_IMAGES: dict[str, pygame.Surface] = {}

# Canvas
screen: pygame.Surface
srect: pygame.Rect
camera: Camera

# Events
events: list[pygame.event.Event]
mouse_pos: pygame.Vector2
mouse_press: tuple[int, ...]
mjr: tuple[int, ...]
mjp: tuple[int, ...]
keys: list[bool]
kp: list[bool]
kr: list[bool]
dt: float
clock: pygame.Clock

# States
next_state: State | None
level_no: int

# Objects
player: Player
tmx_map: pytmx.TiledMap
