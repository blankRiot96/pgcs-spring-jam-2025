import pygame

from src import shared, utils
from src.ui import CoinLineEffect, Flash


class Filth:
    objects: list = []

    SPEED = 30.0
    PLAYER_PROXIMITY_DIST = 100
    JUMP_VELOCITY = -70

    DAMAGE = 0

    def __init__(self, pos, image) -> None:
        Filth.objects.append(self)
        self.image = image
        self.pos = pygame.Vector2(pos)
        self.health = 100
        self.collider = utils.Collider(pos, self.image.get_size())
        utils.Collider.all_colliders.remove(self.collider)
        self.gravity = utils.Gravity()
        self.touched_ground = True

        self.dx, self.dy = 0, 0

    def move(self):
        self.dy += self.gravity.velocity * shared.dt

        dir = 1 if shared.player.collider.pos.x > self.collider.pos.x else -1
        self.dx += Filth.SPEED * dir * shared.dt

    def check_tile_collisions(self):
        collider_data = self.collider.get_collision_data(self.dx, self.dy)

        if (
            utils.CollisionSide.BOTTOM in collider_data.colliders
            or utils.CollisionSide.TOP in collider_data.colliders
        ):
            self.gravity.velocity = 0
            self.dy = 0

        if utils.CollisionSide.BOTTOM in collider_data.colliders:
            self.touched_ground = True

        if (
            utils.CollisionSide.RIGHT in collider_data.colliders
            or utils.CollisionSide.LEFT in collider_data.colliders
        ):
            self.dx = 0

        self.collider.pos += self.dx, self.dy
        self.pos = self.collider.pos

    def check_player_collide(self):
        if self.collider.rect.move(self.dx, self.dy).colliderect(
            shared.player.collider.rect
        ):
            shared.player.health -= Filth.DAMAGE

    def jump(self):
        if (
            self.collider.pos.distance_to(shared.player.collider.pos)
            < Filth.PLAYER_PROXIMITY_DIST
            and self.touched_ground
        ):
            self.gravity.velocity = Filth.JUMP_VELOCITY
            self.touched_ground = False

    def update(self):
        self.gravity.update()
        self.handle_damage()

        self.dx, self.dy = 0, 0
        self.jump()
        self.move()
        self.check_player_collide()
        self.check_tile_collisions()

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
                if self.collider.rect.colliderect(bullet.collider_rect):
                    self.on_bullet_collide(bullet, gun)

            if self.health <= 0:
                try:
                    utils.Collider.all_colliders.remove(self.collider)
                    Filth.objects.remove(self)
                except ValueError:
                    pass

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.collider.pos))
