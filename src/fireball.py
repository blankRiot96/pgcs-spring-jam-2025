import pygame

from src import shared, utils


class FireBall:
    DAMAGE = 100

    def __init__(self, pos, radians, speed) -> None:
        self.image = utils.load_image("assets/fireball.png", True, bound=True)
        self.rect = self.image.get_rect()
        self.speed = speed
        self.radians = radians
        self.pos = pygame.Vector2(pos)
        self.alive = True
        self.boosted = False

    def update(self):
        self.pos = utils.move_towards_rad(
            self.pos, self.radians, self.speed * shared.dt
        )
        self.rect.topleft = self.pos

        if (
            self.pos.x < 0
            or self.pos.y < 0
            or self.pos.x > (shared.tmx_map.width * shared.TILE_SIDE)
            or self.pos.y > (shared.tmx_map.height * shared.TILE_SIDE)
        ):
            self.alive = False

        if self.rect.colliderect(shared.player.collider.rect):
            self.alive = False
            shared.player.health -= FireBall.DAMAGE

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))
        # utils.debug_rect(self.rect)
