import typing as t

import pygame

from src import shared, utils
from src.enums import State


class HellPit:
    objects: list[t.Self] = []
    FALL_SPEED = 10

    def __init__(self, pos, image: pygame.Surface):
        self.pos = pygame.Vector2(pos)
        HellPit.objects.append(self)
        self.image = pygame.transform.scale(
            image, (shared.TILE_SIDE, shared.TILE_SIDE * 10)
        )
        self.rect = self.image.get_rect(topleft=pos)

    def update(self):
        if shared.player.frozen:
            shared.player.collider.pos.y += HellPit.FALL_SPEED * shared.dt

            if (
                shared.player.collider.pos.y
                > shared.srect.height + shared.camera.offset.y
            ):
                if shared.next_state is None:
                    shared.level_no += 1
                    shared.next_state = State.GAME
        elif self.rect.colliderect(shared.player.collider.rect):
            shared.player.frozen = True

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))
