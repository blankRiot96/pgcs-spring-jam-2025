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


class Virtue:
    objects: list[t.Self] = []
    spawner: EntitySpawner

    SPEED = 3
    WING_ROTATE_SPEED = 10
    ATTACK_FOLLOW_SPEED = 50
    ATTACK_TIME = 6.0

    def __init__(self, pos, image: pygame.Surface) -> None:
        Virtue.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.original_image = image
        self.image = image
        self.rect = self.image.get_rect(topleft=self.pos)

        self.spawn_start_time: float | None = None
        self.spawn_animation_timer = utils.Timer(0.2)

        self.white_image = image.copy()
        self.white_image.fill("purple", special_flags=pygame.BLEND_RGBA_ADD)

        self.spawn_images = itertools.cycle([self.white_image, image])

        self.wing_original = pygame.Surface((28, 5), pygame.SRCALPHA)
        self.wing_original.fill(shared.PALETTE["purple"])
        self.wing_1 = pygame.transform.rotate(self.wing_original, 45)
        self.wing_1_rect = self.wing_1.get_rect(center=self.rect.center)
        self.angle_1 = 45

        self.wing_2 = pygame.transform.rotate(self.wing_original, -45)
        self.wing_2_rect = self.wing_2.get_rect(center=self.rect.center)
        self.angle_2 = -45

        self.health = 1000
        self.alive = True

        self.god = utils.load_image("assets/god.png", True)
        self.god.set_alpha(100)
        self.god_rect = self.god.get_rect()
        self.god_center = pygame.Vector2()
        self.god_strike = pygame.Surface(
            (self.god_rect.width, shared.srect.height), pygame.SRCALPHA
        )
        self.god_strike.fill("white")
        self.god_strike.set_alpha(0)
        self.strike_rect = self.god_strike.get_rect(center=self.god_rect.center)
        self.god_alpha = 0
        self.god_start = time.perf_counter()
        self.damage_first = True

        self.first = True

    def move(self):
        self.pos.move_towards_ip(shared.player.collider.pos, Virtue.SPEED * shared.dt)
        self.rect.topleft = self.pos

    def update_wings(self):
        self.angle_1 += Virtue.WING_ROTATE_SPEED * shared.dt
        self.angle_1 %= 360
        self.wing_1 = pygame.transform.rotate(self.wing_original, self.angle_1)
        self.wing_1_rect = self.wing_1.get_rect(center=self.rect.center)

        self.angle_2 -= Virtue.WING_ROTATE_SPEED * shared.dt
        self.angle_2 %= 360
        temp = self.wing_original.copy()
        temp.fill(shared.PALETTE["red2"])
        self.wing_2 = pygame.transform.rotate(temp, self.angle_2)
        self.wing_2_rect = self.wing_2.get_rect(center=self.rect.center)

    def call_heavenly_strike(self):
        if self.first:
            self.god_start = time.perf_counter()
            self.first = False

        god_diff = time.perf_counter() - self.god_start

        if god_diff < Virtue.ATTACK_TIME:
            self.god_alpha = 200 * (god_diff / Virtue.ATTACK_TIME)

        if god_diff <= Virtue.ATTACK_TIME - 0.3:
            self.god_center = pygame.Vector2(shared.player.collider.rect.center)

        self.god_rect.center = self.god_center
        self.strike_rect.centerx = self.god_rect.centerx
        self.strike_rect.centery = shared.player.collider.rect.centery - 7

        if Virtue.ATTACK_TIME <= god_diff < Virtue.ATTACK_TIME + 2.0:
            if self.damage_first:
                self.on_damage_player()
                self.damage_first = False
            self.god_strike.fill(shared.PALETTE["red2"])
            self.god_alpha = 255 * (1 - ((god_diff - Virtue.ATTACK_TIME) / 1.0))

        if god_diff >= Virtue.ATTACK_TIME + 2.0:
            self.god_strike.fill("white")
            self.god_alpha = 0
            self.first = True
            self.damage_first = True

        self.god_strike.set_alpha(int(self.god_alpha))

    def on_damage_player(self):
        if self.strike_rect.colliderect(shared.player.collider.rect):
            shared.player.health -= 500

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
                Virtue.objects.remove(self)
                shared.blood_splatters.append(BloodSplatter(self.rect.center, 100))

            except ValueError:
                pass

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

        self.move()
        self.update_wings()
        self.handle_damage()
        self.call_heavenly_strike()

    def draw(self):
        if not self.spawner.activated:
            return

        shared.screen.blit(self.wing_1, shared.camera.transform(self.wing_1_rect))
        shared.screen.blit(self.wing_2, shared.camera.transform(self.wing_2_rect))
        shared.screen.blit(self.image, shared.camera.transform(self.pos))

        shared.screen.blit(self.god, shared.camera.transform(self.god_rect))
        shared.screen.blit(self.god_strike, shared.camera.transform(self.strike_rect))
