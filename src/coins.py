import typing as t

import pygame

from src import shared, utils


class _Coin:
    objects: list[t.Self] = []

    def __init__(self, pos, image) -> None:
        _Coin.objects.append(self)
        self.image = image
        self.rect = self.image.get_rect()
        drect = pygame.Rect(pos, (shared.TILE_SIDE, shared.TILE_SIDE))
        self.rect.center = drect.center

    def update(self):
        if shared.player.collider.rect.colliderect(self.rect):
            _Coin.objects.remove(self)
            shared.player.coins_collected += 1

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.rect))
