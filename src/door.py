import typing as t

import pygame

from src import shared, utils


class HellPit:
    objects: list[t.Self] = []

    def __init__(self, pos, image):
        self.pos = pygame.Vector2(pos)
        HellPit.objects.append(self)
        self.image = image

    def update(self):
        pass

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))
