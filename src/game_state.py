import pygame

from src import shared, utils
from src.background import Background
from src.enums import State
from src.ui import HUD, FXManager
from src.world import World


class GameState:
    def __init__(self):
        shared.camera = utils.Camera()
        shared.fx_manager = FXManager()
        shared.is_world_frozen = False
        self.background = Background(
            bg_color=shared.PALETTE["black"], line_color=shared.PALETTE["grey"]
        )
        self.world = World()
        self.hud = HUD()
        pygame.mixer.music.load("assets/sounds/26.mp3")
        pygame.mixer.music.play(loops=-1)

    def update(self):
        shared.fx_manager.update()
        if not shared.is_world_frozen:
            self.background.update()
        self.world.update()
        self.hud.update()

    def draw(self):
        if shared.level_no != shared.BOSS_LEVEL:
            self.background.draw()
        else:
            shared.screen.fill(shared.PALETTE["red2"])
        self.world.draw()
        self.hud.draw()
        shared.fx_manager.draw()
