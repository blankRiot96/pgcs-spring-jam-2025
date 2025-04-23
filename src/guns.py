import math
import time
from enum import Enum, auto

import pygame

from src import shared, utils
from src.projectiles import Bullet, Coin


class GunState(Enum):
    GROUND = auto()
    EQUIPPED = auto()
    INVENTORY = auto()


class Shotgun:
    objects = []

    COOLDOWN = 0.7

    def __init__(self, pos, image) -> None:
        Pistol.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = utils.bound_image(image)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.Rect(
            self.pos, (shared.TILE_SIDE, shared.TILE_SIDE)
        ).center
        self.state = GunState.GROUND
        self.bullets: list[Bullet] = []
        self.cooldown = utils.CooldownTimer(Shotgun.COOLDOWN)
        shared.player.guns["shotgun"] = self

    def on_ground(self):
        pass

    def on_inventory(self):
        pass

    def fire_shotgun(self):
        x, y = shared.player.collider.rect.center
        angle = math.atan2(
            (shared.mouse_pos[1] + shared.camera.offset.y) - y,
            (shared.mouse_pos[0] + shared.camera.offset.x) - x,
        )
        angular_space = math.pi / 32
        for offset in range(-2, 3):
            self.bullets.append(
                Bullet(
                    (x, y),
                    angle + (offset * angular_space),
                    200,
                    1.0,
                )
            )

    def update_bullets(self):
        self.cooldown.update()
        if (
            shared.mjp[0] or shared.kp[pygame.K_9]
        ) and not self.cooldown.is_cooling_down:
            self.fire_shotgun()
            self.cooldown.start()

        for bullet in self.bullets[:]:
            bullet.update()

            if not bullet.alive:
                self.bullets.remove(bullet)

    def on_equipped(self):
        self.rect.center = shared.player.collider.rect.center
        self.update_bullets()

    def check_state(self):
        if self.state in (GunState.EQUIPPED, GunState.INVENTORY):
            return

        if self.rect.colliderect(shared.player.collider.rect):
            for gun in shared.player.guns.values():
                if gun.state == GunState.EQUIPPED:
                    gun.state = GunState.INVENTORY
            shared.player.currently_equipped = "shotgun"
            self.state = GunState.EQUIPPED

    def update(self):
        self.check_state()

        if self.state == GunState.EQUIPPED:
            self.on_equipped()

    def draw_gun(self):
        if self.state == GunState.EQUIPPED:
            angle_to_mouse = math.atan2(
                (shared.mouse_pos[1] + shared.camera.offset.y) - self.rect.centery,
                (shared.mouse_pos[0] + shared.camera.offset.x) - self.rect.centerx,
            )
            angle_to_mouse = math.degrees(-angle_to_mouse)

            if -90 < angle_to_mouse < 90:
                image = self.image
            else:
                image = pygame.transform.flip(self.image, False, True)

            rotated_image = pygame.transform.rotate(image, angle_to_mouse)
            shared.screen.blit(rotated_image, shared.camera.transform(self.rect))

        elif self.state == GunState.GROUND:
            shared.screen.blit(self.image, shared.camera.transform(self.rect))

    def draw(self):
        self.draw_gun()

        for bullet in self.bullets:
            bullet.draw()


class Pistol:
    objects = []

    COOLDOWN = 0.1

    def __init__(self, pos, image) -> None:
        Pistol.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = utils.bound_image(image)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.Rect(
            self.pos, (shared.TILE_SIDE, shared.TILE_SIDE)
        ).center
        self.state = GunState.GROUND
        self.coins: list[Coin] = []
        self.bullets: list[Bullet] = []
        self.cooldown = utils.CooldownTimer(Pistol.COOLDOWN)
        shared.player.guns["pistol"] = self

    def on_ground(self):
        pass

    def on_inventory(self):
        pass

    def update_coins(self):
        if shared.mjp[2] or shared.kp[pygame.K_0]:
            self.coins.append(
                Coin.from_mouse(
                    shared.player.collider.rect.center,
                    50,
                    3.0,
                )
            )

        for coin in self.coins[:]:
            coin.update()

            if not coin.alive:
                self.coins.remove(coin)

    def update_bullets(self):
        self.cooldown.update()
        if (
            shared.mjp[0] or shared.kp[pygame.K_9]
        ) and not self.cooldown.is_cooling_down:
            self.bullets.append(
                Bullet.from_mouse(
                    shared.player.collider.rect.center,
                    200,
                    1.0,
                )
            )
            self.cooldown.start()

        for bullet in self.bullets[:]:
            bullet.update()

            if not bullet.alive:
                self.bullets.remove(bullet)

    def on_equipped(self):
        self.rect.center = shared.player.collider.rect.center
        self.update_coins()
        self.update_bullets()

    def check_state(self):
        if self.state in (GunState.EQUIPPED, GunState.INVENTORY):
            return

        if self.rect.colliderect(shared.player.collider.rect):
            for gun in shared.player.guns.values():
                if gun.state == GunState.EQUIPPED:
                    gun.state = GunState.INVENTORY
            shared.player.currently_equipped = "pistol"
            self.state = GunState.EQUIPPED

    def update(self):
        self.check_state()

        if self.state == GunState.EQUIPPED:
            self.on_equipped()

    def draw_gun(self):
        if self.state == GunState.EQUIPPED:
            angle_to_mouse = math.atan2(
                (shared.mouse_pos[1] + shared.camera.offset.y) - self.rect.centery,
                (shared.mouse_pos[0] + shared.camera.offset.x) - self.rect.centerx,
            )
            angle_to_mouse = math.degrees(-angle_to_mouse)

            if -90 < angle_to_mouse < 90:
                image = self.image
            else:
                image = pygame.transform.flip(self.image, False, True)

            rotated_image = pygame.transform.rotate(image, angle_to_mouse)
            shared.screen.blit(rotated_image, shared.camera.transform(self.rect))

        elif self.state == GunState.GROUND:
            shared.screen.blit(self.image, shared.camera.transform(self.rect))

    def draw(self):
        self.draw_gun()

        for coin in self.coins:
            coin.draw()

        for bullet in self.bullets:
            bullet.draw()
