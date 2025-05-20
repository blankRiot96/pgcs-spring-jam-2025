import math
import time
import typing as t

import pygame
import pygame.gfxdraw

from src import shared, utils


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

        pygame.gfxdraw.arc(
            shared.screen,
            int(pos.x),
            int(pos.y),
            PlayerGunCooldownIndicator.RADIUS,
            0,
            int(
                shared.player.guns[  # type: ignore
                    shared.player.currently_equipped
                ].cooldown.amount_cooled
                * 360
            ),  # type: ignore
            (255, 255, 255),
        )


class Flash:
    def __init__(self, duration: float = 0.7) -> None:
        shared.is_world_frozen = True
        self.alive = True
        self.start = time.perf_counter()
        self.image = pygame.Surface(shared.srect.size, pygame.SRCALPHA)
        self.image.fill("white")
        self.image.set_alpha(50)
        self.duration = duration

    def update(self):
        if time.perf_counter() - self.start >= self.duration:
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
        if time.perf_counter() - self.start > shared.fx_manager.flashes[0].duration:
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
        self.fg = utils.load_image("assets/fg2.png", True, bound=True)
        self.bg = utils.load_image("assets/bg2.png", True, bound=True)

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


class NCoinsIndicator:
    def __init__(self, pos) -> None:
        self.pos = pygame.Vector2(pos)
        self.coin_img = utils.load_image("assets/coin.png", True, scale=2.0, bound=True)
        self.width = self.coin_img.get_width()
        self.height = self.coin_img.get_height()
        self.amount_loaded = 1.0

    def update(self):
        if shared.player.n_coins < shared.player.MAX_COINS:
            diff = time.perf_counter() - shared.player.coin_loader_timedown.start
            self.amount_loaded = diff / shared.player.coin_loader_timedown.time_to_pass
        else:
            self.amount_loaded = 1.0

    def draw(self):
        pad_x = 10
        looped = False
        for i in range(shared.player.n_coins):
            shared.screen.blit(
                self.coin_img,
                (self.pos.x + ((self.width + pad_x) * i), self.pos.y),
            )
            looped = True

        if shared.player.n_coins < shared.player.MAX_COINS:
            if not looped:
                i = -1
            pygame.draw.arc(
                shared.screen,
                shared.PALETTE["yellow"],
                (
                    self.pos.x + ((self.width + pad_x) * (i + 1)),
                    self.pos.y,
                    self.width,
                    self.height,
                ),
                0,
                (math.pi * 2) * self.amount_loaded,
                width=self.width,
            )


class HUD:
    def __init__(self) -> None:
        self.cooldown_indicator = PlayerGunCooldownIndicator()
        self.coins_indicator = NCoinsIndicator((10, 265))
        self.player_health_bar = PlayerHealthBar((5, 280))

    def update(self):
        self.cooldown_indicator.update()
        self.player_health_bar.update()
        self.coins_indicator.update()

    def draw(self):
        if shared.player.currently_equipped is not None:
            if shared.player.guns[
                shared.player.currently_equipped
            ].cooldown.is_cooling_down:
                self.cooldown_indicator.draw()

        self.player_health_bar.draw()
        self.coins_indicator.draw()
