import typing as t

import pygame

from src import shared, utils


class Decoration:
    objects: list[t.Self] = []

    def __init__(self, pos, image):
        self.pos = pygame.Vector2(pos)
        Decoration.objects.append(self)
        self.image = image

    def update(self):
        pass

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))


class FGDecoration:
    objects: list[t.Self] = []

    def __init__(self, pos, image):
        self.pos = pygame.Vector2(pos)
        FGDecoration.objects.append(self)
        self.image = image

    def update(self):
        pass

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))


class Note:
    objects: list[t.Self] = []

    def __init__(self, pos, image, text="default text"):
        self.pos = pygame.Vector2(pos)
        Note.objects.append(self)
        self.image = image
        self.rect = self.image.get_rect(topleft=self.pos)
        self.text = text
        self.font = utils.load_font("assets/ultrakill.ttf", 12)
        self.font.align = pygame.FONT_CENTER
        self.text_surf = self.font.render(self.text, False, "white", wraplength=100)
        self.text_surf = utils.bound_image(self.text_surf)
        self.text_rect = self.text_surf.get_rect(
            midbottom=self.rect.midtop + pygame.Vector2(0, -10)
        )

    def update(self):
        pass

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.pos))
        shared.screen.blit(self.text_surf, shared.camera.transform(self.text_rect))

        # utils.debug_rect(self.rect)
        # utils.debug_rect(self.text_rect)
