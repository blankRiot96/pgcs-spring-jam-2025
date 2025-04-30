import typing as t

import pygame

from src import shared, utils

side_inverts = {
    "midtop": "midbottom",
    "midbottom": "midtop",
    "midleft": "midright",
    "midright": "midleft",
}


class Portal:
    objects: list[t.Self] = []
    other: t.Self

    def __init__(self, pos, image: pygame.Surface, side: str, id: int) -> None:
        Portal.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = image
        self.rect = self.image.get_rect(topleft=self.pos)
        self.side = side
        self.id = id

    def update(self):
        if shared.player.collider.rect.colliderect(self.rect):
            # print(shared.player.collider.rect)
            rect = shared.player.collider.rect.copy()
            setattr(
                rect,
                side_inverts[self.other.side],
                getattr(self.other.rect, self.other.side),
            )

            shared.player.collider.pos = pygame.Vector2(rect.topleft)

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))


class GravityWell:
    objects: list[t.Self] = []
    MAX_GRAVITY = 200

    def __init__(self, pos, width, height, acc) -> None:
        GravityWell.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.rect = pygame.Rect(self.pos, (width, height))
        self.acc = acc

        color = "red" if acc > 0 else "blue"
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.image.fill(color)
        self.image.set_alpha(150 * abs(acc / GravityWell.MAX_GRAVITY))

    def update(self):
        if shared.player.collider.rect.colliderect(self.rect):
            shared.player.gravity.velocity += self.acc * shared.dt

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.rect))
