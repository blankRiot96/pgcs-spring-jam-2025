import typing as t

import pygame

from src import shared, utils


class EntitySpawner:
    objects: list[t.Self] = []

    def __init__(self, pos, width, height) -> None:
        self.pos = pygame.Vector2(pos)
        self.rect = pygame.Rect(self.pos, (width, height))
        self.activated = False
        EntitySpawner.objects.append(self)

    def update(self):
        if shared.player.collider.rect.colliderect(self.rect):
            self.activated = True

    def draw(self):
        utils.debug_rect(self.rect)
