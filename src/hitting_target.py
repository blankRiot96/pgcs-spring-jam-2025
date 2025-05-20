import pygame

from src import shared


class HittingTarget:
    objects: list = []

    def __init__(self, pos, image) -> None:
        HittingTarget.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = image
        self.rect = self.image.get_rect(topleft=self.pos)
        self.health = 1000

    def update(self):
        for gun in shared.player.guns.values():
            for bullet in gun.bullets:
                if self.rect.colliderect(bullet.collider_rect):
                    self.health -= 50
                    gun.bullets.remove(bullet)

            if self.health <= 0:
                try:
                    HittingTarget.objects.remove(self)
                except ValueError:
                    pass

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))
