import pygame

from src import shared, utils
from src.enums import State


class GameOverState:
    def __init__(self) -> None:
        self.font = utils.load_font("assets/ultrakill.ttf", 32)
        self.text = self.font.render("[YOU ARE DEAD]", False, "white")
        self.trect = self.text.get_rect(
            center=shared.srect.center - pygame.Vector2(0, 100)
        )

        self.skull = utils.load_image("assets/skull.png", True)
        self.skrect = self.skull.get_rect(center=shared.srect.center)

        self.restart = self.font.render("Press [R] TO RESTART", False, "white")
        self.rrect = self.restart.get_rect(
            center=shared.srect.center + pygame.Vector2(0, 100)
        )

    def update(self):
        if shared.kp[pygame.K_r]:
            shared.next_state = State.GAME

    def draw(self):
        shared.screen.fill("black")
        shared.screen.blit(self.text, self.trect)

        shared.screen.blit(self.skull, self.skrect)

        shared.screen.blit(self.restart, self.rrect)
