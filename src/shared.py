from __future__ import annotations

import typing as t

import pygame
import pytmx

if t.TYPE_CHECKING:
    from src.blood_splatter import BloodSplatter
    from src.enums import State
    from src.fireball import FireBall
    from src.player import Player
    from src.projectiles import Bullet, Coin, CoreEject, Explosion, Magnet, Sawblade
    from src.ui import FXManager
    from src.utils import Camera

# Const
TILE_SIDE = 16
WORLD_GRAVITY = 100
MAX_FALL_VELOCITY = 300
PALETTE: dict[t.Literal["purple", "grey", "black", "yellow", "red", "red2"], str] = {
    "black": "#202020",
    "grey": "#393939",
    "purple": "#725956",
    "yellow": "#f6cd26",
    "red": "#5a2721",
    "red2": "#531811",
}
ENTITY_CLASS_IMAGES: dict[str, pygame.Surface] = {}
BOSS_LEVEL = 2

# Canvas
screen: pygame.Surface
srect: pygame.Rect
camera: Camera

# Events
events: list[pygame.event.Event]
mouse_pos: pygame.Vector2
mouse_press: tuple[int, ...]
mjr: tuple[bool, ...]
mjp: tuple[bool, ...]
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
fx_manager: FXManager
pistol_bullets: list[Bullet]
shotgun_bullets: list[Bullet]
sawblades: list[Sawblade]
coins: list[Coin]
fireballs: list[FireBall]
cores: list[CoreEject]
explosions: list[Explosion]
blood_splatters: list[BloodSplatter]
magnets: list[Magnet]

# Flags
is_world_frozen: bool


# Config
save_data: dict[str, list[str]]
