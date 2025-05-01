from __future__ import annotations

import itertools
import time
import typing as t

import pygame

from src import shared, utils
from src.fireball import FireBall
from src.ui import CoinLineEffect, Flash

if t.TYPE_CHECKING:
    from src.spawner import EntitySpawner


class Soldier:
    objects: list[t.Self] = []
    spawner: EntitySpawner

    DAMAGE = 200

    def __init__(self, pos, image: pygame.Surface) -> None:
        Soldier.objects.append(self)
        self.original_image = image
        self.image = image
        self.pos = pygame.Vector2(pos)
        self.health = 100
        self.rect = self.image.get_rect(topleft=self.pos)
        self.gravity = utils.Gravity()
        self.touched_ground = True

        self.spawn_start_time: float | None = None
        self.spawn_animation_timer = utils.Timer(0.2)

        self.white_image = image.copy()
        self.white_image.fill("purple", special_flags=pygame.BLEND_RGBA_ADD)

        self.spawn_images = itertools.cycle([self.white_image, image])

        self.charge_timer = utils.CooldownTimer(3.0)
        self.fireball_image = utils.load_image("assets/fireball.png", True, bound=True)
        self.fireball_rect = self.fireball_image.get_rect(midbottom=self.rect.midtop)
        self.fireballs: list[FireBall] = []

        self.first_spawn = True

    def handle_punch(self):
        if (
            shared.player.punch_timer.is_cooling_down
            and pygame.Vector2(self.rect.center).distance_to(
                shared.player.collider.rect.center
            )
            < 32
        ):
            self.health -= 100

    def fireball(self):
        self.charge_timer.update()

        if self.charge_timer.is_cooling_down:
            return

        self.fireballs.append(
            FireBall(
                self.fireball_rect.topleft,
                -utils.rad_to(
                    pygame.Vector2(self.fireball_rect.center),
                    pygame.Vector2(shared.player.collider.rect.center),
                ),
                30,
            )
        )
        self.charge_timer.start()

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
                self.charge_timer.start()
                self.first_spawn = False

        self.gravity.update()
        self.handle_damage()
        self.handle_punch()
        self.fireball()

        for fireball in self.fireballs[:]:
            fireball.update()

            if not fireball.alive:
                self.fireballs.remove(fireball)

    def on_bullet_collide(self, bullet, gun):
        self.health -= bullet.damage
        gun.bullets.remove(bullet)

        if bullet.coin_history:
            points = [shared.player.collider.pos] + bullet.coin_history + [self.pos]
            shared.fx_manager.coin_lines.append(CoinLineEffect(points))
            shared.fx_manager.flashes.append(Flash())

    def handle_damage(self):
        for gun in shared.player.guns.values():
            for bullet in gun.bullets:
                if self.rect.colliderect(bullet.collider_rect):
                    self.on_bullet_collide(bullet, gun)

        if self.health <= 0:
            try:
                Soldier.objects.remove(self)
            except ValueError:
                pass

    def draw(self):
        if not self.spawner.activated:
            return

        shared.screen.blit(self.image, shared.camera.transform(self.pos))

        if self.charge_timer.is_cooling_down:
            morphed = pygame.transform.scale_by(
                self.fireball_image, self.charge_timer.amount_cooled
            )
            mrect = morphed.get_rect(center=self.fireball_rect.center)

            shared.screen.blit(morphed, shared.camera.transform(mrect))

        for fireball in self.fireballs:
            fireball.draw()
