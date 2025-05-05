import pygame

from src import shared, utils
from src.enums import State


class WinState:
    def create_scene(self, text: str) -> pygame.Surface:
        surf = pygame.Surface((600, 300))
        text_surf = self.font.render(text, False, shared.PALETTE["yellow"])
        surf.blit(text_surf, text_surf.get_rect(center=shared.srect.center))

        return surf

    def __init__(self) -> None:
        self.font = utils.load_font("assets/ultrakill.ttf", 20)
        self.font.align = pygame.FONT_CENTER
        self.current_scene = self.create_scene("YOU HAVE AVENGED HUMANITY")

    def update(self):
        pass

    def draw(self):
        shared.screen.blit(self.current_scene, (0, 0))
