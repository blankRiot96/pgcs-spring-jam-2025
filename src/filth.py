from __future__ import annotations

import itertools
import time
import typing as t

import pygame

from src import shared, utils
from src.blood_splatter import BloodSplatter
from src.ui import CoinLineEffect, Flash

if t.TYPE_CHECKING:
    from src.spawner import EntitySpawner
    from src.tiles import Tile


class FilthyArea:
    def __init__(self, pos, width, height) -> None:
        self.pos = pygame.Vector2(pos)
        self.rect = pygame.Rect(self.pos, (width, height))
        self.tiles = []


class Filth:
    objects: list[t.Self] = []
    spawner: EntitySpawner
    filthy_area: FilthyArea

    SPEED = 30.0
    PLAYER_PROXIMITY_DIST = 100
    JUMP_VELOCITY = -70

    DAMAGE = 100

    def __init__(self, pos, image: pygame.Surface) -> None:
        Filth.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.original_image = image
        self.image = image
        self.health = 100
        self.rect = image.get_rect(topleft=self.pos)
        self.gravity = utils.Gravity()
        self.touched_ground = True

        self.spawn_start_time: float | None = None
        self.spawn_animation_timer = utils.Timer(0.2)

        self.white_image = image.copy()
        self.white_image.fill("purple", special_flags=pygame.BLEND_RGBA_ADD)

        self.spawn_images = itertools.cycle([self.white_image, image])

        self.dx, self.dy = 0, 0
        self.damage_cooldown = utils.CooldownTimer(0.5)

    def move(self):
        self.dy += self.gravity.velocity * shared.dt

        dir = 1 if shared.player.collider.pos.x > self.pos.x else -1
        self.dx += Filth.SPEED * dir * shared.dt

    def check_tile_collisions(self):
        for tile in self.filthy_area.tiles:
            if tile.rect.colliderect(self.rect.move(0, self.dy)):
                self.gravity.velocity = 0
                self.dy = 0

                if self.dy > 0:
                    self.touched_ground = True

            if tile.rect.colliderect(self.rect.move(self.dx, 0)):
                self.dx = 0

        if not self.filthy_area.rect.colliderect(self.rect.move(self.dx, 0)):
            self.dx = 0
        if not self.filthy_area.rect.colliderect(self.rect.move(0, self.dy)):
            self.dy = 0

        self.pos += self.dx, self.dy

    def check_player_collide(self):
        self.damage_cooldown.update()
        if (
            self.rect.move(self.dx, self.dy).colliderect(shared.player.collider.rect)
            and not self.damage_cooldown.is_cooling_down
        ):
            shared.player.health -= Filth.DAMAGE
            self.damage_cooldown.start()

    def jump(self):
        if (
            self.pos.distance_to(shared.player.collider.pos)
            < Filth.PLAYER_PROXIMITY_DIST
            and self.touched_ground
        ):
            self.gravity.velocity = Filth.JUMP_VELOCITY
            self.touched_ground = False

    def handle_punch(self):
        if (
            shared.player.just_punched
            and pygame.Vector2(self.rect.center).distance_to(
                shared.player.collider.rect.center
            )
            < 32
        ):
            self.health -= shared.player.PUNCH_DAMAGE

    def is_out_of_view(self):
        return not shared.camera.rect.colliderect(self.rect)

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

        self.handle_damage()

        if self.is_out_of_view():
            return
        self.dx, self.dy = 0, 0
        self.gravity.update()
        self.jump()
        self.move()
        self.check_player_collide()
        self.check_tile_collisions()
        self.handle_punch()
        self.rect.topleft = self.pos

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
        if self.health <= 0:
            try:
                Filth.objects.remove(self)
                shared.blood_splatters.append(BloodSplatter(self.rect.center, 100))
            except ValueError:
                pass

    def draw(self):
        if not self.spawner.activated:
            return

        shared.screen.blit(self.image, shared.camera.transform(self.pos))
