import typing as t

import pygame

from src import shared, utils
from src.guns import GunState, Pistol, Shotgun


class Player:
    JUMP_VELOCITY = -150
    MAX_HORIZONTAL_SPEED = 40

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

    def move(self):
        dx, dy = 0, 0
        self.gravity.update()

        if shared.kp[pygame.K_SPACE]:
            self.gravity.velocity = Player.JUMP_VELOCITY

        dy += self.gravity.velocity * shared.dt

        dx += shared.keys[pygame.K_d] - shared.keys[pygame.K_a]
        dx *= Player.MAX_HORIZONTAL_SPEED * shared.dt

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
        self.move()
        self.check_gun_swap(pygame.K_q, "pistol")
        self.check_gun_swap(pygame.K_e, "shotgun")

    def draw(self):
        image = (
            self.image
            if self.last_direction == "right"
            else pygame.transform.flip(self.image, True, False)
        )
        shared.screen.blit(image, shared.camera.transform(self.collider.rect))
