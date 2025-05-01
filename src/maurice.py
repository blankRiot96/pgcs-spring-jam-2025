from __future__ import annotations

import itertools
import time
import typing as t

import pygame

from src import shared, utils
from src.blood_splatter import BloodSplatter
from src.fireball import FireBall
from src.ui import CoinLineEffect, Flash

if t.TYPE_CHECKING:
    from src.spawner import EntitySpawner


class Maurice:
    objects: list[t.Self] = []
    spawner: EntitySpawner

    SPEED = 2

    def __init__(self, pos, image: pygame.Surface) -> None:
        Maurice.objects.append(self)
        self.original_image = image
        self.image = image
        self.pos = pygame.Vector2(pos)
        self.health = 500
        self.rect = self.image.get_rect(topleft=self.pos)

        self.spawn_start_time: float | None = None
        self.spawn_animation_timer = utils.Timer(0.2)

        self.white_image = image.copy()
        self.white_image.fill("purple", special_flags=pygame.BLEND_RGBA_ADD)

        self.spawn_images = itertools.cycle([self.white_image, image])

        self.first_spawn = True

        self.triplet_spawn_start = time.perf_counter()
        self.gate1, self.gate2 = True, True

    def handle_punch(self):
        if (
            shared.player.punch_timer.is_cooling_down
            and pygame.Vector2(self.rect.center).distance_to(
                shared.player.collider.rect.center
            )
            < 32
        ):
            self.health -= 100

    def create_fireball(self):
        shared.fireballs.append(
            FireBall(
                self.rect.center,
                -utils.rad_to(
                    pygame.Vector2(self.rect.center),
                    pygame.Vector2(shared.player.collider.rect.center),
                ),
                40,
            )
        )

    def fireball(self):
        diff = time.perf_counter() - self.triplet_spawn_start
        if diff > 3.5:
            self.create_fireball()
            self.gate1 = True
            self.gate2 = True
            self.triplet_spawn_start = time.perf_counter()

        elif diff > 3.25 and self.gate2:
            self.create_fireball()
            self.gate2 = False

        elif diff > 3 and self.gate1:
            self.create_fireball()
            self.gate1 = False

    def move(self):
        self.pos.move_towards_ip(
            shared.player.collider.rect.center, Maurice.SPEED * shared.dt
        )
        self.rect.topleft = self.pos

    def update(self):
        if not self.spawner.activated:
            return
        elif self.spawn_start_time is None:
            self.spawn_start_time = time.perf_counter()

        if time.perf_counter() - self.spawn_start_time < 0.7:
            if self.spawn_animation_timer.tick():
                self.image = next(self.spawn_images)
            return
        else:
            self.image = self.original_image

            if self.first_spawn:
                self.first_spawn = False

        self.handle_damage()
        self.handle_punch()
        self.fireball()

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

        for fireball in shared.fireballs:
            if not fireball.boosted:
                continue

            if fireball.rect.colliderect(self.rect):
                self.health -= fireball.DAMAGE
                fireball.alive = False

        if self.health <= 0:
            try:
                Maurice.objects.remove(self)
                shared.blood_splatters.append(BloodSplatter(self.rect.center, 100))

            except ValueError:
                pass

    def draw(self):
        if not self.spawner.activated:
            return

        shared.screen.blit(self.image, shared.camera.transform(self.pos))
