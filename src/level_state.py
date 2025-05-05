import random

import pygame

from src import shared, utils
from src.background import Background
from src.enums import State


class LevelWidget:
    HOVER_EFFECT_SPEED = 0.25
    WIGGLE_SPEED = 2

    def __init__(self, pos: tuple[int, int], level_no: int, level_name: str) -> None:
        self.level_no = level_no
        self.pos = pygame.Vector2(pos)
        self.locked = self.level_no > shared.save_data["max_level"]
        if not self.locked:
            self.image = utils.load_image(
                "assets/level_widget_base.png", True, bound=True
            ).copy()
        else:
            self.image = utils.load_image(
                "assets/locked_level.png", True, bound=True
            ).copy()

        self.rect = self.image.get_rect(topleft=self.pos)
        self.font = utils.load_font(None, 32)
        self.sixteen_font = utils.load_font(None, 16)
        self.sixteen_font.align = pygame.FONT_CENTER
        self.last_frame_hover_status = False
        self.expanding = False
        self.scale_vector = pygame.Vector2(1.0, 0)

        self.offset_vector = pygame.Vector2()
        self.gen_random_target_offset()

        if not self.locked:
            self.draw_info(level_no, level_name)

    def gen_random_target_offset(self):
        self.random_target_offset = pygame.Vector2(
            random.randint(-5, 5), random.randint(-5, 5)
        )

    def draw_info(self, level_no: int, level_name: str):
        level_image = utils.load_image(f"assets/level_{level_no}.png", False)
        level_image = pygame.transform.scale(level_image, (100, 70))

        self.image.blit(level_image, (10, 5))

        level_no_surf = self.font.render(
            f"0-{level_no}", False, shared.PALETTE["purple"]
        )
        name_surf = self.sixteen_font.render(
            level_name,
            False,
            shared.PALETTE["purple"],
            wraplength=self.image.get_width() - 50,
        )
        x, y = self.image.get_rect().midbottom
        name_rect = name_surf.get_rect(midbottom=(x, y - 20))

        self.image.blit(level_no_surf, (50, 90))
        self.image.blit(name_surf, name_rect)

    def handle_hover(self):
        if self.expanding:
            self.scale_vector.move_towards_ip(
                (1.1, 0), LevelWidget.HOVER_EFFECT_SPEED * shared.dt
            )
        else:
            self.scale_vector.move_towards_ip(
                (1.0, 0), LevelWidget.HOVER_EFFECT_SPEED * shared.dt
            )

    def update(self):
        hovering = self.rect.collidepoint(shared.mouse_pos)
        if not hovering and self.last_frame_hover_status:
            self.expanding = False
        elif hovering and not self.last_frame_hover_status:
            self.expanding = True

        self.last_frame_hover_status = hovering
        clicked = shared.mjp[0]

        self.handle_hover()

        if hovering and clicked and not self.locked:
            shared.level_no = self.level_no
            shared.next_state = State.GAME

        self.offset_vector.move_towards_ip(
            self.random_target_offset, LevelWidget.WIGGLE_SPEED * shared.dt
        )

        if self.offset_vector == self.random_target_offset:
            self.gen_random_target_offset()

    def draw(self):
        image = pygame.transform.scale_by(self.image, self.scale_vector.x)
        rect = image.get_rect(center=self.rect.center)
        # print(self.offset_vector)
        shared.screen.blit(image, self.offset_vector + rect.topleft)


class LevelState:
    def __init__(self) -> None:
        self.widgets: list[LevelWidget] = [
            LevelWidget((20, 60), 1, "INTO THE FIRE"),
            LevelWidget((160, 60), 2, "SOMETHING WICKED"),
            LevelWidget((310, 60), 3, "AN ANGEL'S VIRTUE"),
            LevelWidget((450, 60), 4, "AESTHETICS OF HATE"),
        ]

        self.background = Background(
            bg_color=shared.PALETTE["black"], line_color=shared.PALETTE["grey"]
        )

    def update(self):
        self.background.update()
        for widget in self.widgets:
            widget.update()

    def draw(self):
        self.background.draw()
        for widget in self.widgets:
            widget.draw()
