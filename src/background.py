import math

import pygame

from src import shared, utils


class Line:
    SPEED = 50
    WIDTH = 30

    def __init__(self) -> None:
        self.v1 = pygame.Vector2(-Line.WIDTH, -Line.WIDTH)
        self.v2 = pygame.Vector2(-Line.WIDTH, -Line.WIDTH)
        self.c = 0
        self.alive = True
        self.distance = 0

    def update(self):
        self.v1.x += Line.SPEED * shared.dt
        self.v1.x = min(self.v1.x, shared.srect.width)
        self.v2.y = (shared.srect.height + Line.WIDTH) * (
            self.v1.x / shared.srect.width
        )

        center = pygame.Vector2(self.v1.x + self.v2.x, self.v1.y + self.v2.y) * 0.5
        self.distance = center.distance_to((0, 0))

        if self.v1.x == shared.srect.width:
            self.v1, self.v2 = self.v2, self.v1
            self.c += 1

        if self.c == 2:
            self.alive = False

    def draw(self, color):
        pygame.draw.line(shared.screen, color, self.v1, self.v2, width=Line.WIDTH)


class Background:
    def __init__(self, bg_color, line_color) -> None:
        self.lines: list[Line] = [Line()]
        self.header = self.lines[0]
        self.bg_color = bg_color
        self.line_color = line_color

    def update(self):
        if self.header.distance >= Line.WIDTH * 2:
            self.lines.append(Line())
            self.header = self.lines[-1]

        for line in self.lines[:]:
            line.update()
            if not line.alive:
                self.lines.remove(line)

    def draw(self):
        shared.screen.fill(self.bg_color)
        for line in self.lines:
            line.draw(self.line_color)
