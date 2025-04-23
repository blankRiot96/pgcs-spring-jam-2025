from src import shared, utils
from src.background import Background
from src.enums import State
from src.ui import HUD
from src.world import World


class GameState:
    def __init__(self):
        shared.camera = utils.Camera()
        self.background = Background(
            bg_color=shared.PALETTE["purple"], line_color=shared.PALETTE["grey"]
        )
        self.world = World()
        self.hud = HUD()

    def update(self):
        self.background.update()
        self.world.update()
        self.hud.update()

    def draw(self):
        self.background.draw()
        self.world.draw()
        self.hud.draw()
