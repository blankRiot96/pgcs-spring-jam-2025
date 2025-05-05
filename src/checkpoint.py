import time
import typing as t

import pygame

from src import shared, utils


class Checkpoint:
    objects: list[t.Self] = []

    def __init__(self, pos, image: pygame.Surface) -> None:
        Checkpoint.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = image
        self.rect = self.image.get_rect(topleft=self.pos)
        self.font = utils.load_font("assets/ultrakill.ttf", 12)
        self.surf = self.font.render("Checkpoint!", False, shared.PALETTE["yellow"])
        self.scale = 0.1
        self.start = time.perf_counter()
        self.performing_effect = False

    def update(self):
        if (
            self.rect.colliderect(shared.player.collider.rect)
            and shared.last_checkpoint is not self
        ):
            shared.last_checkpoint = self
            self.start = time.perf_counter()
            self.performing_effect = True

    def perform_effect(self):
        max_y_offset = -10
        expand_time = 0.1

        diff = time.perf_counter() - self.start
        if diff > 1.5:
            self.performing_effect = False
        elif diff > expand_time:
            fade_ratio = (diff - expand_time) / 1.0
            fade_ratio = min(1.0, fade_ratio)
            fade_ratio = 1 - fade_ratio

            surf = self.surf.copy()
            surf.set_alpha(int(255 * fade_ratio))
            rect = surf.get_rect(
                midbottom=self.rect.midtop + pygame.Vector2(0, max_y_offset)
            )

            shared.screen.blit(surf, shared.camera.transform(rect))
        else:
            self.scale = diff / expand_time
            self.scale = min(1.0, self.scale)
            text_surf = pygame.transform.scale_by(self.surf, self.scale)
            rect = text_surf.get_rect(midbottom=self.rect.midtop)

            y_offset = max_y_offset * self.scale
            shared.screen.blit(
                text_surf, shared.camera.transform(rect.move(0, y_offset))
            )

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))

        if self.performing_effect:
            self.perform_effect()
