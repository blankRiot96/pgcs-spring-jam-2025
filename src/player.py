import math
import time
import typing as t

import pygame

from src import shared, utils
from src.enums import State
from src.guns import GunState, Pistol, Shotgun


class Player:
    JUMP_VELOCITY = -150
    MAX_HORIZONTAL_SPEED = 40
    MAX_HEALTH = 1000
    DASH_DURATION = 0.3
    DASH_VELOCITY = 200

    objects: list[t.Self] = []
    guns: dict[str, Pistol | Shotgun] = {}

    def __init__(self, pos, image):
        shared.player = self
        self.image = utils.bound_image(image)
        self.collider = utils.Collider(pos, self.image.get_size())
        self.gravity = utils.Gravity()
        self.coins_collected = 0
        self.last_direction: t.Literal["right", "left"] = "right"
        self.currently_equipped: str | None = None
        self.frozen = False
        self.sliding = False
        self.punch_timer = utils.CooldownTimer(0.1)
        self.punch_angle = 0.0
        self.pg_dwn = False

        self.health = Player.MAX_HEALTH
        self.dashing = False
        self.dash_cooldown = utils.CooldownTimer(0.1)
        self.start_dash = time.perf_counter()
        self.dash_radians = 0.0

    def move(self):
        self.dash_cooldown.update()
        if time.perf_counter() - self.start_dash > Player.DASH_DURATION:
            self.dashing = False

        if shared.mjp[3]:
            self.pg_dwn = True

        if shared.mjr[3]:
            self.pg_dwn = False

        self.sliding = (
            shared.keys[pygame.K_s] or shared.keys[pygame.K_LCTRL] or self.pg_dwn
        ) and not self.dashing

        dx, dy = 0, 0
        self.gravity.update()

        if not self.dashing:
            if shared.kp[pygame.K_SPACE] or shared.kp[pygame.K_w]:
                self.gravity.velocity = Player.JUMP_VELOCITY
            dx += shared.keys[pygame.K_d] - shared.keys[pygame.K_a]
            dx *= Player.MAX_HORIZONTAL_SPEED * shared.dt

        dy += self.gravity.velocity * shared.dt

        # if not self.dash_cooldown.is_cooling_down and shared.kp[pygame.K_LSHIFT]:
        #     self.dashing = True
        #     self.dash_cooldown.start()
        #     self.start_dash = time.perf_counter()
        #     self.dash_radians = utils.rad_to(
        #         self.collider.pos, self.collider.pos + (dx, dy)
        #     )

        if self.sliding:
            dx *= 2
            dy += 100 * shared.dt

        if self.dashing:
            dx = Player.DASH_VELOCITY * math.cos(self.dash_radians) * shared.dt
            dy = Player.DASH_VELOCITY * math.sin(self.dash_radians) * shared.dt

        collider_data = self.collider.get_collision_data(dx, dy)
        if (
            utils.CollisionSide.BOTTOM in collider_data.colliders
            or utils.CollisionSide.TOP in collider_data.colliders
        ):
            self.gravity.velocity = 0
            dy = 0

        if (
            utils.CollisionSide.RIGHT in collider_data.colliders
            or utils.CollisionSide.LEFT in collider_data.colliders
        ):
            dx = 0

        self.collider.pos += dx, dy

        if dx > 0:
            self.last_direction = "right"
        elif dx < 0:
            self.last_direction = "left"

        shared.camera.attach_to(self.collider.pos, smoothness_factor=1)

    def punch(self):
        self.punch_timer.update()
        if shared.kp[pygame.K_f]:
            self.punch_timer.start()
            self.punch_angle = math.degrees(
                utils.rad_to_mouse(self.collider.rect.center)
            )

    def switch_gun_to(self, gun_name: str):
        for gname, gun in shared.player.guns.items():
            if gname == gun_name:
                self.currently_equipped = gun_name
                gun.state = GunState.EQUIPPED
                continue

            if gun.state == GunState.EQUIPPED:
                gun.state = GunState.INVENTORY

    def check_gun_swap(self, key, gun_name):
        if shared.kp[key]:
            gun = shared.player.guns[gun_name]
            if gun.state in (GunState.EQUIPPED, GunState.GROUND):
                return
            elif gun.state == GunState.INVENTORY:
                self.switch_gun_to(gun_name)

    def update(self):
        if self.frozen:
            return

        self.move()
        self.punch()
        self.check_gun_swap(pygame.K_q, "pistol")
        self.check_gun_swap(pygame.K_e, "shotgun")

        if self.health <= 0:
            shared.next_state = State.GAME_OVER

    def draw(self):
        image = (
            self.image
            if self.last_direction == "right"
            else pygame.transform.flip(self.image, True, False)
        )

        if self.sliding:
            if self.last_direction == "right":
                angle = 45
            else:
                angle = -45
            image = pygame.transform.rotate(image, angle)

        shared.screen.blit(image, shared.camera.transform(self.collider.rect))

        if self.punch_timer.is_cooling_down:
            image = shared.ENTITY_CLASS_IMAGES["Punch"]
            image = pygame.transform.rotate(
                image, math.degrees(-utils.rad_to_mouse(self.collider.rect.center))
            )
            rect = image.get_rect(center=self.collider.rect.center)
            shared.screen.blit(image, shared.camera.transform(rect))
