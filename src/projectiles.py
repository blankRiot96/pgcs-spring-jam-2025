from __future__ import annotations

import math
import time

import pygame

from src import shared, utils
from src.filth import Filth
from src.soldier import Soldier
from src.virtue import Virtue


class Bullet:
    def __init__(self, pos, radians, speed, seconds, damage) -> None:
        self.pos = pygame.Vector2(pos)
        self.radians = radians
        self.speed = speed
        self.collider_rect = pygame.Rect(self.pos, (10, 10))
        self.seconds = seconds
        self.alive = True
        self.target: pygame.Vector2 | None = None
        self.damage = damage

        self.coin_history: list[pygame.Vector2] = []

        self.start = time.perf_counter()

    @classmethod
    def from_mouse(cls, pos, speed, seconds, damage):
        return cls(
            pos,
            math.atan2(
                (shared.mouse_pos[1] + shared.camera.offset.y) - pos[1],
                (shared.mouse_pos[0] + shared.camera.offset.x) - pos[0],
            ),
            speed,
            seconds,
            damage,
        )

    def get_closest_entity(self, entities, reject=None) -> tuple[Coin, float] | None:
        closest_dist = None
        closest_entity = None

        for entity in entities:
            if entity is reject:
                continue

            dist = entity.pos.distance_to(self.pos)
            if closest_dist is None or (dist < closest_dist):
                closest_entity = entity
                closest_dist = dist

        if closest_entity is None or closest_dist is None:
            return None

        return closest_entity, closest_dist

    def update(self):
        if self.target is None:
            self.pos.x += math.cos(self.radians) * self.speed * shared.dt
            self.pos.y += math.sin(self.radians) * self.speed * shared.dt
        else:
            self.pos.move_towards_ip(self.target, self.speed * shared.dt)

        self.collider_rect.center = self.pos

        if self.speed <= 0:
            self.alive = False

        if (time.perf_counter() - self.start) > self.seconds:
            self.alive = False

    def draw(self):
        pygame.draw.line(
            shared.screen,
            shared.PALETTE["yellow"],
            shared.camera.transform(self.pos),
            shared.camera.transform(
                utils.move_towards_rad(self.pos, -self.radians, 10)
            ),
        )

        # utils.debug_rect(self.coin_collide_rect)


class Coin:
    MAX_TAIL_SIZE = 15
    MAX_SIZE_SECONDS = 1.0

    def __init__(self, pos, radians, speed, seconds) -> None:
        self.pos = pygame.Vector2(pos)
        self.radians = radians
        self.original_speed = speed
        self.speed = speed
        self.seconds = seconds
        self.start = time.perf_counter()
        self.direction = self.radians
        self.alive = True
        self.image = utils.load_image("assets/coin.png", True, bound=True)
        self.rect = self.image.get_rect()
        self.rcenter = pygame.Vector2(self.rect.center)

        self.dx = math.cos(self.radians) * self.speed
        self.dy = math.sin(self.radians) * self.speed

        self.trail_points: list[pygame.Vector2] = []

    @classmethod
    def from_mouse(cls, pos, speed, seconds):
        return cls(
            pos,
            math.atan2(
                (shared.mouse_pos[1] + shared.camera.offset.y) - pos[1],
                (shared.mouse_pos[0] + shared.camera.offset.x) - pos[0],
            ),
            speed,
            seconds,
        )

    def redirect_to_enemy(self, target, bullet):
        bullet.target = target.pos
        bullet.damage *= 2
        bullet.radians = utils.rad_to(bullet.pos, target.pos)

    def redirect_to_coin(self, coin, bullet):
        bullet.target = coin.pos
        bullet.radians = utils.rad_to(bullet.pos, coin.rcenter)
        bullet.damage *= 2
        bullet.coin_history.append(coin.pos)

    def on_bullet_collide(self):
        for bullet in shared.player.guns["pistol"].bullets:
            if self.rect.colliderect(bullet.collider_rect):
                closest_coin = bullet.get_closest_entity(
                    shared.player.guns["pistol"].coins, reject=self  # type: ignore
                )
                closest_target = bullet.get_closest_entity(
                    [
                        obj
                        for obj in Filth.objects + Virtue.objects + Soldier.objects
                        if obj.spawner.activated
                    ]
                )

                if closest_coin is not None:
                    coin, dist_to_coin = closest_coin

                if closest_target is not None:
                    target, dist_to_target = closest_target

                if closest_coin is None:
                    if closest_target is None:
                        bullet.alive = False
                    else:
                        self.redirect_to_enemy(target, bullet)
                else:
                    if closest_target is None:
                        self.redirect_to_coin(coin, bullet)
                    else:
                        if dist_to_target < dist_to_coin:  # type: ignore
                            self.redirect_to_enemy(target, bullet)
                        else:
                            self.redirect_to_coin(coin, bullet)

                self.alive = False
                return

    def update(self):
        self.rect.center = self.pos
        self.rcenter = pygame.Vector2(self.rect.center)
        self.on_bullet_collide()

        start = self.pos.copy()
        self.dy += (shared.WORLD_GRAVITY / 10) * shared.dt
        self.pos += pygame.Vector2(self.dx, self.dy) * shared.dt
        self.direction = utils.rad_to(start, self.pos)

        if time.perf_counter() - self.start >= self.seconds:
            self.alive = False

    def points(self) -> list[pygame.Vector2]:
        ratio = min(1, (time.perf_counter() - self.start) / Coin.MAX_SIZE_SECONDS)
        tail_size = Coin.MAX_TAIL_SIZE * ratio

        head = self.pos.copy()
        tail = utils.move_towards_rad(head, -self.direction, tail_size)

        angle_offset = math.pi / 64
        left_wing = utils.move_towards_rad(
            head, -self.direction - angle_offset, tail_size / 1.1
        )

        right_wing = utils.move_towards_rad(
            head, -self.direction + angle_offset, tail_size / 1.1
        )

        return [left_wing, head, right_wing, tail]

    def draw(self):
        points = self.points()
        pygame.draw.polygon(
            shared.screen,
            "white",
            [shared.camera.transform(pos) for pos in points],
        )
        self.rect.center = utils.get_mid_point(points[0], points[2])
        shared.screen.blit(self.image, shared.camera.transform(self.rect))
