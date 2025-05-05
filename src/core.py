import json
import sys

import pygame

from src import shared
from src.states import StateManager


class Core:
    def __init__(self) -> None:
        self.win_init()
        with open("save-data/data.json") as f:
            shared.save_data = json.load(f)
        shared.level_no = 2
        self.state_manager = StateManager()

    def win_init(self):
        pygame.init()

        if len(sys.argv) > 1 and sys.argv[1] == "-d":
            flags = 0
        else:
            flags = pygame.FULLSCREEN | pygame.SCALED

        shared.screen = pygame.display.set_mode((600, 300), flags, vsync=1)
        shared.srect = shared.screen.get_rect()
        shared.clock = pygame.Clock()

    def get_events(self):
        shared.events = pygame.event.get()
        shared.dt = shared.clock.tick() / 1000
        shared.dt = max(shared.dt, 0.1)
        shared.keys = pygame.key.get_pressed()
        shared.kp = pygame.key.get_just_pressed()
        shared.kr = pygame.key.get_just_released()
        shared.mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        shared.mjr = pygame.mouse.get_just_released()
        shared.mjp = pygame.mouse.get_just_pressed()
        shared.mouse_press = pygame.mouse.get_pressed()

    def write_save_data(self):
        with open("assets/save-data/data.json", "w") as f:
            json.dump(shared.save_data, f, indent=2)

    def check_for_exit(self):
        for event in shared.events:
            if event.type == pygame.QUIT:
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit

    def update(self):
        self.get_events()
        self.check_for_exit()
        self.state_manager.update()

    def draw(self):
        shared.screen.fill("black")
        self.state_manager.draw()
        pygame.display.flip()

    def run(self):
        while True:
            self.update()
            self.draw()


def main():
    core = Core()
    core.run()
