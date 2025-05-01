import time

import pygame

from src import shared, utils


class BloodSplatter:
    RADIUS = 16 * 2
    DURATION = 0.7

    def __init__(self, center, heal) -> None:
        self.center = pygame.Vector2(center)
        self.image = utils.circle_surf(BloodSplatter.RADIUS, "red")
        self.image.set_alpha(70)
        self.rect = self.image.get_rect(center=self.center)

        self.start = time.perf_counter()
        self.alive = True
        self.received_health = False
        self.heal = heal

    def update(self):
        if not self.received_health and shared.player.collider.rect.colliderect(
            self.rect
        ):
            shared.player.health += self.heal
            shared.player.health = min(shared.player.health, shared.player.MAX_HEALTH)
            self.received_health = True

        diff = time.perf_counter() - self.start
        amount = diff / BloodSplatter.DURATION

        if amount >= 1:
            self.alive = False

        amount = min(1.0, amount)

        alpha = (1 - amount) * 70
        self.image.set_alpha(int(alpha))

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.rect))
