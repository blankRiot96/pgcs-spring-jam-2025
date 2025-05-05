import pygame

from src import shared, utils
from src.enums import State


class IntroState:
    def create_scene(self, text: str) -> pygame.Surface:
        surf = pygame.Surface((600, 300))
        text_surf = self.font.render(text, False, "red")
        surf.blit(text_surf, text_surf.get_rect(center=shared.srect.center))

        return surf

    def __init__(self) -> None:
        self.font = utils.load_font("assets/ultrakill.ttf", 20)
        self.font.align = pygame.FONT_CENTER
        texts = [
            "Gabriel visits Earth.",
            "He finds people killing and torturing each other.\n\nGabriel is disgusted.",
            "GABRIEL KILLS EVERYBODY\n\nEARTH IS NOW HELL\n\nAVENGE HUMANITY",
        ]
        self.scenes = iter(self.create_scene(text) for text in texts)
        self.current_scene = next(self.scenes)

        help = "PRESS TAB TO END\nCLICK ANYWHERE TO GO NEXT"
        self.text_surf = utils.load_font("assets/ultrakill.ttf", 12).render(
            help, False, "red", "black"
        )

    def update(self):
        if shared.kp[pygame.K_TAB]:
            shared.next_state = State.LEVEL_SELECTOR
        if shared.mjp[0]:
            try:
                self.current_scene = next(self.scenes)
            except StopIteration:
                shared.next_state = State.LEVEL_SELECTOR

    def draw(self):
        shared.screen.blit(self.current_scene, (0, 0))
        shared.screen.blit(self.text_surf, (10, 10))
