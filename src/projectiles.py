from __future__ import annotations

import math
import time

import pygame

from src import shared, utils
from src.filth import Filth
from src.gabriel import Gabriel
from src.maurice import Maurice
from src.soldier import Soldier
from src.tiles import Tile
from src.virtue import Virtue


class Magnet:
    GIGGLE_RADIUS = 16 * 3

    def __init__(self, pos, radians, speed, seconds) -> None:
        self.pos = pygame.Vector2(pos)
        self.radians = radians
        self.original_speed = speed
        self.speed = speed
        self.seconds = seconds
        self.start = time.perf_counter()
        self.direction = self.radians
        self.alive = True
        self.image = utils.load_image("assets/magnet.png", True, bound=True)
        self.rect = self.image.get_rect(topleft=self.pos)

        self.dx = math.cos(self.radians) * self.speed
        self.dy = math.sin(self.radians) * self.speed

        self.trail_points: list[pygame.Vector2] = []
        self.anchor_entity = None
        self.diff_from_center = pygame.Vector2()

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

    def update(self):
        if self.anchor_entity is None:
            start = self.pos.copy()
            self.dy += (shared.WORLD_GRAVITY / 8) * shared.dt

            self.pos += pygame.Vector2(self.dx, self.dy) * shared.dt
            self.direction = utils.rad_to(start, self.pos)
        else:
            self.pos = (
                pygame.Vector2(self.anchor_entity.rect.center) - self.diff_from_center
            )

        self.rect.topleft = self.pos

        for obj in (
            Filth.objects
            + Maurice.objects
            + Soldier.objects
            + Virtue.objects
            + Tile.objects
            + Gabriel.objects
        ):
            if obj.rect.colliderect(self.rect) and self.anchor_entity is None:
                self.anchor_entity = obj
                self.diff_from_center = self.anchor_entity.rect.center - self.pos

        if time.perf_counter() - self.start >= self.seconds:
            self.alive = False

    def draw(self):
        image = pygame.transform.rotate(self.image, math.degrees(-self.direction))
        shared.screen.blit(image, shared.camera.transform(self.rect))


class Sawblade:
    ROTATE_SPEED = 1

    def __init__(self, pos, radians, speed, seconds, damage) -> None:
        self.pos = pygame.Vector2(pos)
        self.radians = radians
        self.speed = speed
        self.seconds = seconds
        self.alive = True
        self.damage = damage
        self.image = utils.load_image("assets/nail.png", True, bound=True).copy()
        self.image = pygame.transform.rotate(self.image, -math.degrees(self.radians))
        self.rect = self.image.get_rect(topleft=self.pos)
        self.start = time.perf_counter()
        self.magnet: Magnet | None = None

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
        if self.magnet is None:
            for magnet in shared.magnets:
                if (
                    pygame.Vector2(magnet.rect.center).distance_to(self.rect.center)
                    <= Magnet.GIGGLE_RADIUS
                ):
                    self.magnet = magnet
                    self.seconds = magnet.seconds - (time.perf_counter() - magnet.start)

        if self.magnet is None:
            self.pos.x += math.cos(self.radians) * self.speed * shared.dt
            self.pos.y += math.sin(self.radians) * self.speed * shared.dt
        else:
            self.radians += Sawblade.ROTATE_SPEED * shared.dt
            self.pos.x = self.magnet.rect.centerx + (
                math.cos(self.radians) * Magnet.GIGGLE_RADIUS
            )
            self.pos.y = self.magnet.rect.centery + (
                math.sin(-self.radians) * Magnet.GIGGLE_RADIUS
            )

        self.rect.topleft = self.pos

        if self.speed <= 0:
            self.alive = False

        diff = time.perf_counter() - self.start
        ratio = diff / self.seconds
        self.image.set_alpha(int(255 * (1 - ratio)))
        if diff > self.seconds:
            self.alive = False

    def draw(self):
        if self.magnet is None:
            image = self.image
        else:
            image = pygame.transform.rotate(self.image, math.degrees(self.radians) + 90)
        shared.screen.blit(image, shared.camera.transform(self.pos))


class Explosion:
    RADIUS = 16 * 5
    DURATION = 2.0
    DAMAGE = 500

    def __init__(self, center) -> None:
        self.center = pygame.Vector2(center)
        self.image = utils.circle_surf(Explosion.RADIUS, shared.PALETTE["yellow"])
        self.image.set_alpha(150)
        self.rect = self.image.get_rect(center=self.center)

        self.start = time.perf_counter()
        self.first = True
        self.alive = True

    def update(self):
        if self.first:
            shared.sounds["explosion"].play()
            for obj in (
                Filth.objects
                + Maurice.objects
                + Soldier.objects
                + Virtue.objects
                + Gabriel.objects
            ):
                if obj.rect.colliderect(self.rect):
                    obj.health -= Explosion.DAMAGE

            self.first = False

        diff = time.perf_counter() - self.start
        amount = diff / Explosion.DURATION

        if amount >= 1:
            self.alive = False

        amount = min(1.0, amount)

        alpha = (1 - amount) * 150
        self.image.set_alpha(int(alpha))

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.rect))


class CoreEject:
    MAX_TAIL_SIZE = 15
    MAX_SIZE_SECONDS = 0.4

    def __init__(self, pos, radians, speed, seconds) -> None:
        self.pos = pygame.Vector2(pos)
        self.radians = radians
        self.original_speed = speed
        self.speed = speed
        self.seconds = seconds
        self.start = time.perf_counter()
        self.direction = self.radians
        self.alive = True
        self.image = utils.load_image("assets/core_eject.png", True, bound=True)
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

    def update(self):
        self.rect.center = self.pos
        self.rcenter = pygame.Vector2(self.rect.center)

        start = self.pos.copy()
        self.dy += (shared.WORLD_GRAVITY / 4) * shared.dt

        self.pos += pygame.Vector2(self.dx, self.dy) * shared.dt
        self.direction = utils.rad_to(start, self.pos)

        for obj in (
            Filth.objects
            + Maurice.objects
            + Soldier.objects
            + Virtue.objects
            + Gabriel.objects
        ):
            if obj.rect.colliderect(self.rect):
                self.alive = False

        if time.perf_counter() - self.start >= self.seconds:
            self.alive = False

        if not self.alive:
            shared.explosions.append(Explosion(self.rect.center))

    def points(self) -> list[pygame.Vector2]:
        ratio = min(1, (time.perf_counter() - self.start) / CoreEject.MAX_SIZE_SECONDS)
        tail_size = CoreEject.MAX_TAIL_SIZE * ratio

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
            shared.PALETTE["yellow"],
            [shared.camera.transform(pos) for pos in points],
        )
        self.rect.center = utils.get_mid_point(points[0], points[2])
        shared.screen.blit(self.image, shared.camera.transform(self.rect))


class Bullet:
    def __init__(self, pos, radians, speed, seconds, damage) -> None:
        self.pos = pygame.Vector2(pos)
        self.radians = radians
        self.speed = speed
        self.collider_rect = pygame.Rect(self.pos, (10, 10))
        self.seconds = seconds
        self.alive = True
        self.target: pygame.Vector2 | None = None
        self.base_damage = damage
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
        bullet.damage += bullet.base_damage
        bullet.radians = utils.rad_to(bullet.pos, target.pos)

    def redirect_to_coin(self, coin, bullet):
        bullet.target = coin.pos
        bullet.radians = utils.rad_to(bullet.pos, coin.rcenter)
        bullet.damage += bullet.base_damage
        bullet.coin_history.append(coin.pos)

    def on_bullet_collide(self):
        for bullet in shared.pistol_bullets:
            if self.rect.colliderect(bullet.collider_rect):
                closest_coin = bullet.get_closest_entity(
                    shared.coins,
                    reject=self,  # type: ignore
                )
                closest_target = bullet.get_closest_entity(
                    [
                        obj
                        for obj in Filth.objects
                        + Virtue.objects
                        + Soldier.objects
                        + Maurice.objects
                        + Gabriel.objects
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
