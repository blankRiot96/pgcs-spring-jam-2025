import math
import typing as t

import pygame

from src import shared, utils
from src.enums import State
from src.guns import GunState, Pistol, SawbladeLauncher, Shotgun
from src.ui import Flash


class Player:
    JUMP_VELOCITY = -150
    MAX_HORIZONTAL_SPEED = 40
    MAX_HEALTH = 1000
    DASH_DURATION = 0.3
    DASH_VELOCITY = 200
    MAX_COINS = 4
    PUNCH_DAMAGE = 30

    objects: list[t.Self] = []
    guns: dict[str, Pistol | Shotgun | SawbladeLauncher] = {}

    def __init__(self, pos, image):
        shared.player = self
        self.image = utils.bound_image(image)
        self.collider = utils.Collider(pos, self.image.get_size())
        utils.Collider.all_colliders.remove(self.collider)
        self.gravity = utils.Gravity()
        self.coins_collected = 0
        self.last_direction: t.Literal["right", "left"] = "right"
        self.currently_equipped: str | None = None
        self.frozen = False
        self.sliding = False
        self.punch_timer = utils.CooldownTimer(0.1)
        self.punch_angle = 0.0
        self.just_punched = False
        self.punch_cooldown = utils.CooldownTimer(0.7)
        self.pg_dwn = False
        self.punch_image = utils.load_image("assets/fist.png", True, bound=True)
        self.jumps = 0
        self.health = Player.MAX_HEALTH
        self.n_coins = Player.MAX_COINS
        self.coin_loader_timedown = utils.Timer(1.0)

    def move(self):
        if shared.mjp[3]:
            self.pg_dwn = True

        if shared.mjr[3]:
            self.pg_dwn = False

        self.sliding = (
            shared.keys[pygame.K_s] or shared.keys[pygame.K_LCTRL] or self.pg_dwn
        )

        dx, dy = 0, 0
        self.gravity.update()

        if (shared.kp[pygame.K_SPACE] or shared.kp[pygame.K_w]) and self.jumps < 2:
            self.jumps += 1
            self.gravity.velocity = Player.JUMP_VELOCITY
            shared.sounds["jump"].play()

        dx += shared.keys[pygame.K_d] - shared.keys[pygame.K_a]
        dx *= Player.MAX_HORIZONTAL_SPEED * shared.dt

        dy += self.gravity.velocity * shared.dt

        if self.sliding:
            dx *= 2
            dy += 100 * shared.dt

        collider_data = self.collider.get_collision_data(dx, dy)
        if (
            utils.CollisionSide.BOTTOM in collider_data.colliders
            or utils.CollisionSide.TOP in collider_data.colliders
        ):
            self.gravity.velocity = 0
            dy = 0

        if utils.CollisionSide.BOTTOM in collider_data.colliders:
            self.jumps = 0

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

        if self.collider.pos.y > (shared.tmx_map.height * shared.TILE_SIDE) + 1200:
            self.health = 0

    def punch(self):
        self.just_punched = False
        self.punch_cooldown.update()
        self.punch_timer.update()
        if shared.kp[pygame.K_f] and not self.punch_cooldown.is_cooling_down:
            self.punch_cooldown.start()
            self.just_punched = True
            self.punch_timer.start()
            self.punch_angle = math.degrees(
                utils.rad_to_mouse(self.collider.rect.center)
            )

        if self.punch_timer.is_cooling_down:
            for fireball in shared.fireballs:
                if fireball.boosted:
                    continue

                if (
                    pygame.Vector2(fireball.rect.center).distance_to(
                        self.collider.rect.center
                    )
                    < 40
                ):
                    shared.fx_manager.flashes.append(Flash(0.3))
                    fireball.radians = -utils.rad_to_mouse(self.collider.rect.center)
                    fireball.speed *= 2
                    fireball.boosted = True
                    self.health = Player.MAX_HEALTH

    def switch_gun_to(self, gun_name: str):
        for gname, gun in shared.player.guns.items():
            if gname == gun_name:
                self.currently_equipped = gun_name
                gun.state = GunState.EQUIPPED
                continue

            if gun.state == GunState.EQUIPPED:
                gun.state = GunState.INVENTORY

    def check_gun_swap(self, key, gun_name):
        if shared.kp[key] and self.guns.get(gun_name) is not None:
            gun = self.guns[gun_name]
            if gun.state in (GunState.EQUIPPED, GunState.GROUND):
                return
            elif gun.state == GunState.INVENTORY:
                self.switch_gun_to(gun_name)

    def load_coins(self):
        if self.coin_loader_timedown.tick() and self.n_coins < Player.MAX_COINS:
            self.n_coins += 1

    def update(self):
        if self.frozen:
            return

        self.load_coins()
        self.move()
        self.punch()
        self.check_gun_swap(pygame.K_q, "pistol")
        self.check_gun_swap(pygame.K_e, "shotgun")
        self.check_gun_swap(pygame.K_x, "sawblade")

        if self.health <= 0:
            shared.next_state = State.GAME_OVER

    def draw_fist(self):
        if self.punch_timer.is_cooling_down:
            image = self.punch_image
            image = pygame.transform.rotate(
                image, math.degrees(-utils.rad_to_mouse(self.collider.rect.center))
            )
            rect = image.get_rect(center=self.collider.rect.center)
            shared.screen.blit(image, shared.camera.transform(rect))

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
        # utils.debug_rect(self.collider.rect)
