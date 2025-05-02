import math
import random
import time
import typing as t
from enum import Enum, auto

import pygame

from src import shared, utils
from src.projectiles import Bullet, Coin, CoreEject, Magnet, Sawblade


class GunState(Enum):
    GROUND = auto()
    EQUIPPED = auto()
    INVENTORY = auto()


class SawbladeLauncher:
    objects: list[t.Self] = []

    COOLDOWN = 0.2

    def __init__(self, pos, image) -> None:
        SawbladeLauncher.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = utils.bound_image(image)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.Rect(
            self.pos, (shared.TILE_SIDE, shared.TILE_SIDE)
        ).center
        self.state = GunState.GROUND
        self.cooldown = utils.CooldownTimer(SawbladeLauncher.COOLDOWN)
        shared.player.guns["sawblade"] = self

    def on_ground(self):
        pass

    def on_inventory(self):
        pass

    def fire(self):
        x, y = shared.player.collider.rect.center
        blade = Sawblade.from_mouse((x, y), 200, 0.2, 30)
        shared.sawblades.append(blade)

    def update_bullets(self):
        self.cooldown.update()
        if shared.mouse_press[0] and not self.cooldown.is_cooling_down:
            self.fire()
            self.cooldown.start()

    def on_equipped(self):
        self.rect.center = shared.player.collider.rect.center
        self.update_bullets()

        if shared.mjp[2]:
            shared.magnets.append(Magnet.from_mouse(self.rect.center, 50, 7.0))

    def check_state(self):
        if self.state in (GunState.EQUIPPED, GunState.INVENTORY):
            return

        if self.rect.colliderect(shared.player.collider.rect):
            for gun in shared.player.guns.values():
                if gun.state == GunState.EQUIPPED:
                    gun.state = GunState.INVENTORY
            shared.player.currently_equipped = "sawblade"
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


class Shotgun:
    objects = []

    COOLDOWN = 0.7

    def __init__(self, pos, image) -> None:
        Shotgun.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = utils.bound_image(image)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.Rect(
            self.pos, (shared.TILE_SIDE, shared.TILE_SIDE)
        ).center
        self.state = GunState.GROUND
        self.cooldown = utils.CooldownTimer(Shotgun.COOLDOWN)
        shared.player.guns["shotgun"] = self

        self.charging_alt = False
        self.charged_amount = 0
        self.charge_start = time.perf_counter()

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
        angular_space = math.pi / 128
        for offset in range(-2, 3):
            shared.shotgun_bullets.append(
                Bullet(
                    (x, y),
                    angle + (offset * angular_space),
                    200,
                    1.0,
                    70,
                )
            )

    def update_bullets(self):
        self.cooldown.update()
        if (
            shared.mjp[0] or shared.kp[pygame.K_9]
        ) and not self.cooldown.is_cooling_down:
            self.fire_shotgun()
            self.cooldown.start()

    def on_equipped(self):
        self.rect.center = shared.player.collider.rect.center

        self.charging_alt = shared.mouse_press[2]
        if shared.mjp[2]:
            self.charge_start = time.perf_counter()

        if self.charging_alt:
            diff = time.perf_counter() - self.charge_start
            self.charged_amount = (diff - 0.5) / 1.3
            self.charged_amount = min(1, self.charged_amount)
            self.charged_amount = max(0, self.charged_amount)

        if shared.mjr[2]:
            shared.cores.append(
                CoreEject.from_mouse(
                    shared.player.collider.rect.center, 100 * self.charged_amount, 0.5
                )
            )
            self.charged_amount = 0

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

    def draw_alt_charge_indicator(self):
        if not (self.charging_alt and self.state == GunState.EQUIPPED):
            return

        height = self.charged_amount * 12
        color = pygame.Color("white").lerp(
            shared.PALETTE["yellow"], self.charged_amount
        )
        rect = pygame.Rect((0, 0), (3, height))
        px, py = shared.player.collider.rect.midleft
        shake_pixels = self.charged_amount * 2
        rect.midright = (px - 5, py) + pygame.Vector2(
            shake_pixels * random.randint(-1, 1), shake_pixels * random.randint(-1, 1)
        )
        pygame.draw.rect(shared.screen, color, shared.camera.transform(rect))

    def draw(self):
        self.draw_gun()
        self.draw_alt_charge_indicator()


class Pistol:
    objects = []

    COOLDOWN = 1.0

    def __init__(self, pos, image) -> None:
        Pistol.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = utils.bound_image(image)
        self.rect = self.image.get_rect()
        self.rect.center = pygame.Rect(
            self.pos, (shared.TILE_SIDE, shared.TILE_SIDE)
        ).center
        self.state = GunState.GROUND
        self.cooldown = utils.CooldownTimer(Pistol.COOLDOWN)
        shared.player.guns["pistol"] = self

    def on_ground(self):
        pass

    def on_inventory(self):
        pass

    def update_coins(self):
        if shared.mjp[2] or shared.kp[pygame.K_0]:
            shared.coins.append(
                Coin.from_mouse(
                    shared.player.collider.rect.center,
                    50,
                    3.0,
                )
            )

    def update_bullets(self):
        self.cooldown.update()
        if (
            shared.mjp[0] or shared.kp[pygame.K_9]
        ) and not self.cooldown.is_cooling_down:
            shared.pistol_bullets.append(
                Bullet.from_mouse(shared.player.collider.rect.center, 200, 1.0, 200)
            )
            self.cooldown.start()

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
