import itertools
import random

import pygame

from src import shared, utils


class GrassBlade:
    def __init__(self, pos):
        pos = pygame.Vector2(pos)
        self.original_image = utils.load_image(
            f"assets/grass_blade_{random.randint(1, 5)}.png", True, bound=True
        )
        self.original_rect = self.original_image.get_rect()
        pos.y += 32 - self.original_rect.height
        self.original_rect.topleft = pos
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(topleft=pos)

    def update(self, sway_amt):
        if self.rect.colliderect(shared.player.collider.rect):
            self.with_player = True
            side = -1 if self.rect.x > shared.player.collider.pos.x else 1
            self.image = pygame.transform.rotate(self.original_image, 45 * side)
            self.rect = self.image.get_rect(midbottom=self.original_rect.midbottom)
        else:
            self.image = pygame.transform.rotate(self.original_image, sway_amt)
            self.rect = self.image.get_rect(midbottom=self.original_rect.midbottom)

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.rect))


class GrassBatch:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        n = 15
        self.blades: list[GrassBlade] = [
            GrassBlade((self.pos.x + i * (shared.TILE_SIDE / n), self.pos.y + 7))
            for i in range(n)
        ]
        self.sway_vec = pygame.Vector2(0, 0)
        self.sway_targets = itertools.cycle([-20, 20])
        self.current_target = next(self.sway_targets)

    def update(self):
        if self.sway_vec.x == self.current_target:
            self.current_target = next(self.sway_targets)

        self.sway_vec.move_towards_ip((self.current_target, 0), 1.5 * shared.dt)

        for blade in self.blades:
            blade.update(self.sway_vec.x)

    def draw(self):
        for blade in self.blades:
            blade.draw()
