import math
import time
import typing as t

import pygame
import pygame.gfxdraw

from src import shared, utils

# class CoinCounter:
#     def __init__(self, pos) -> None:
#         self.pos = pygame.Vector2(pos)
#         self.image = pygame.transform.scale_by(shared.ENTITY_CLASS_IMAGES["Coin"], 1.5)
#         self.image_rect = self.image.get_rect(topleft=self.pos)
#         self.font = utils.load_font(None, 16)

#     def update(self):
#         pass

#     def draw(self):
#         shared.screen.blit(self.image, self.image_rect)

#         text_surf = self.font.render(
#             f"{shared.player.coins_collected}x", False, "white"
#         )
#         text_rect = text_surf.get_rect()
#         text_rect.midleft = self.image_rect.midright + pygame.Vector2(5, 1)

#         shared.screen.blit(text_surf, text_rect)


class PlayerGunCooldownIndicator:
    RADIUS = 5

    def __init__(self) -> None:
        pass

    def update(self):
        pass

    def draw(self):
        pos = shared.camera.transform(
            (
                int(shared.player.collider.pos.x - 10),
                int(shared.player.collider.pos.y - 10),
            )
        )
        rect = pygame.draw.circle(
            shared.screen,
            shared.PALETTE["grey"],
            pos,
            PlayerGunCooldownIndicator.RADIUS,
        )
        # pygame.draw.arc(
        #     shared.screen,
        #     "white",
        #     rect.inflate(-1, -1),
        #     0,
        #     shared.player.gun.cooldown.amount_cooled * (math.pi * 2),
        #     PlayerGunCooldownIndicator.RADIUS,
        # )
        pygame.gfxdraw.arc(
            shared.screen,
            int(pos.x),
            int(pos.y),
            PlayerGunCooldownIndicator.RADIUS,
            0,
            int(shared.player.guns[shared.player.currently_equipped].cooldown.amount_cooled * 360),  # type: ignore
            (255, 255, 255),
        )


class Flash:
    DURATION = 0.7

    def __init__(self) -> None:
        shared.is_world_frozen = True
        self.alive = True
        self.start = time.perf_counter()
        self.image = pygame.Surface(shared.srect.size, pygame.SRCALPHA)
        self.image.fill("white")
        self.image.set_alpha(50)

    def update(self):
        if time.perf_counter() - self.start >= Flash.DURATION:
            shared.is_world_frozen = False
            self.alive = False

    def draw(self):
        shared.screen.blit(self.image, (0, 0))


class CoinLineEffect:
    def __init__(self, coin_history: list[pygame.Vector2]) -> None:
        self.coin_history = coin_history
        self.start = time.perf_counter()
        self.alive = True

    def update(self):
        if time.perf_counter() - self.start > Flash.DURATION:
            self.alive = False

    def draw(self):
        for start, end in zip(self.coin_history[:-1], self.coin_history[1:]):
            pygame.draw.line(
                shared.screen,
                shared.PALETTE["yellow"],
                shared.camera.transform(start),
                shared.camera.transform(end),
                2,
            )


class FXManager:
    def __init__(self) -> None:
        self.coin_lines: list[CoinLineEffect] = []
        self.flashes: list[Flash] = []

    def update(self):
        for line in self.coin_lines[:]:
            line.update()

            if not line.alive:
                self.coin_lines.remove(line)

        for flash in self.flashes[:]:
            flash.update()

            if not flash.alive:
                self.flashes.remove(flash)

    def draw(self):
        for line in self.coin_lines:
            line.draw()

        for flash in self.flashes:
            flash.draw()


class PlayerHealthBar:
    def __init__(self, pos: t.Sequence) -> None:
        self.pos = pygame.Vector2(pos)
        self.fg = utils.load_image("assets/health_bar_fg.png", True, bound=True)
        self.bg = utils.load_image("assets/health_bar_bg.png", True, bound=True)

        self.image = self.fg.copy()

    def update(self):
        if shared.player.health <= 0:
            return
        ratio = shared.player.health / shared.player.MAX_HEALTH
        width = self.fg.get_width() * ratio

        self.image = self.fg.subsurface((0, 0, width, self.fg.get_height()))

    def draw(self):
        shared.screen.blit(self.bg, self.pos)
        shared.screen.blit(self.image, self.pos)


class HUD:
    def __init__(self) -> None:
        self.cooldown_indicator = PlayerGunCooldownIndicator()
        self.player_health_bar = PlayerHealthBar((10, 270))

    def update(self):
        self.cooldown_indicator.update()
        self.player_health_bar.update()

    def draw(self):
        if shared.player.currently_equipped is not None:
            if shared.player.guns[
                shared.player.currently_equipped
            ].cooldown.is_cooling_down:
                self.cooldown_indicator.draw()

        self.player_health_bar.draw()
