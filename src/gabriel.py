import math
import random
import time
import typing as t
from dataclasses import dataclass, field
from enum import Enum, auto

import pygame

from src import shared, utils
from src.blood_splatter import BloodSplatter
from src.fireball import FireBall
from src.tiles import Tile
from src.ui import CoinLineEffect, Flash


class Attack(Enum):
    DROPPING = auto()
    DUAL_SWORD_TOSS = auto()
    FIREBALLS = auto()
    RAIN_OF_SWORDS = auto()


class Spawner:
    def __init__(self) -> None:
        self.activated = True


@dataclass
class DualTossData:
    anchor: pygame.Vector2


@dataclass
class DroppingData:
    start: float = field(default_factory=time.perf_counter)
    wait_duration: float = 0.2
    positioned: bool = False
    vel_y: float = 0.0
    damage: int = 100


@dataclass
class FireballData:
    start: float = field(default_factory=time.perf_counter)
    cooldown_between_fireball: float = 0.2
    cooldown_between_streak: float = 1.0

    cooldown: utils.Timer = utils.Timer(cooldown_between_fireball)
    streak_cooldown: utils.CooldownTimer = utils.CooldownTimer(cooldown_between_streak)

    n_fireballs: int = 3
    n: int = 0


class Gabriel:
    SPEED = 1.5

    objects: list[t.Self] = []
    spawner = Spawner()

    dropping_data: DroppingData
    fireball_data: FireballData

    def __init__(self, pos, image: pygame.Surface) -> None:
        Gabriel.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = utils.load_image("assets/gabriel.png", True, bound=True)
        dummy_rect = pygame.Rect(self.pos, (16, 16))
        self.rect = self.image.get_rect(midbottom=dummy_rect.midbottom)
        self.health = 10_000
        self.sword = utils.load_image("assets/sword.png", True, bound=True)
        self.sword_rect = self.sword.get_rect()
        self.sway_rad = random.randint(-90, 90)

        self.enraged = False
        self.move_rng_timer = utils.Timer(5.0)
        self.attack_rng_timer = utils.Timer(3.0)
        self.rng_attack()

    def on_bullet_collide(self, bullet):
        self.health -= bullet.damage
        bullet.alive = False

        if bullet.coin_history:
            points = [shared.player.collider.pos] + bullet.coin_history + [self.pos]
            shared.fx_manager.coin_lines.append(CoinLineEffect(points))
            shared.fx_manager.flashes.append(Flash())

    def handle_damage(self):
        for bullet in shared.shotgun_bullets + shared.pistol_bullets:
            if self.rect.colliderect(bullet.collider_rect):
                self.on_bullet_collide(bullet)

        for blade in shared.sawblades:
            if blade.rect.colliderect(self.rect):
                self.health -= blade.damage

        for fireball in shared.fireballs:
            if not fireball.boosted:
                continue

            if fireball.rect.colliderect(self.rect):
                self.health -= fireball.DAMAGE
                fireball.alive = False

        if self.health <= 5000:
            self.enraged = True

        if self.health <= 0:
            try:
                Gabriel.objects.remove(self)
                shared.blood_splatters.append(BloodSplatter(self.rect.center, 100))
            except ValueError:
                pass

    def rng_movement(self):
        if self.move_rng_timer.tick():
            self.sway_rad = random.randint(-90, 90)

    def move(self):
        if self.attack != Attack.DROPPING:
            self.pos.move_towards_ip(
                shared.player.collider.pos, Gabriel.SPEED * shared.dt
            )
            self.pos = utils.move_towards_rad(
                self.pos, self.sway_rad, Gabriel.SPEED * shared.dt
            )
        self.rect.topleft = self.pos

    def rng_attack(self):
        options = [Attack.DROPPING, Attack.DUAL_SWORD_TOSS, Attack.FIREBALLS]
        if self.enraged:
            options.append(Attack.RAIN_OF_SWORDS)

        # self.attack = random.choice(options)
        self.attack = Attack.DUAL_SWORD_TOSS

        if self.attack == Attack.DROPPING:
            self.dropping_data = DroppingData()
        elif self.attack == Attack.FIREBALLS:
            self.fireball_data = FireballData()

    def layered_rng_attack(self):
        if not self.attack_rng_timer.tick() or self.attack == Attack.DROPPING:
            return

        self.attack_rng_timer.time_to_pass = random.uniform(3.0, 7.0)
        self.rng_attack()

    def attack_dropping(self):
        diff = time.perf_counter() - self.dropping_data.start

        if (
            diff < self.dropping_data.wait_duration
            and not self.dropping_data.positioned
        ):
            self.rect.centerx = shared.player.collider.rect.centerx
            self.pos.x = self.rect.x
            self.pos.y = shared.player.collider.pos.y - (16 * 7)
            self.rect.topleft = self.pos
            self.dropping_data.positioned = True
        elif diff >= self.dropping_data.wait_duration:
            self.dropping_data.vel_y += 30.0 * shared.dt
            self.pos.y += self.dropping_data.vel_y * shared.dt

            hit_tiles = False
            for tile in Tile.objects:
                if tile.rect.colliderect(self.rect):
                    hit_tiles = True
                    break

            if self.rect.colliderect(shared.player.collider.rect):
                shared.player.health -= self.dropping_data.damage
                self.rng_attack()
            elif hit_tiles:
                self.rng_attack()

    def attack_dual_sword_toss(self):
        pass

    def attack_fireballs(self):
        self.fireball_data.streak_cooldown.update()

        if self.fireball_data.streak_cooldown.is_cooling_down:
            return

        if not self.fireball_data.cooldown.tick():
            return

        shared.fireballs.append(
            FireBall(
                self.rect.center,
                -utils.rad_to(
                    pygame.Vector2(self.rect.center),
                    pygame.Vector2(shared.player.collider.rect.center),
                ),
                100.0,
            )
        )
        self.fireball_data.n += 1

        if self.fireball_data.n >= 3:
            self.fireball_data.streak_cooldown.start()
            self.fireball_data.n = 0

    def attack_rain_of_swords(self):
        pass

    def on_attack(self):
        if self.attack == Attack.DROPPING:
            self.attack_dropping()
        elif self.attack == Attack.DUAL_SWORD_TOSS:
            self.attack_dual_sword_toss()
        elif self.attack == Attack.FIREBALLS:
            self.attack_fireballs()
        elif self.attack == Attack.RAIN_OF_SWORDS:
            self.attack_rain_of_swords()

    def update(self):
        self.rng_movement()
        self.move()
        self.layered_rng_attack()
        self.on_attack()
        self.handle_damage()

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.rect))
