import math

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


class HUD:
    def __init__(self) -> None:
        self.cooldown_indicator = PlayerGunCooldownIndicator()

    def update(self):
        self.cooldown_indicator.update()

    def draw(self):
        if shared.player.currently_equipped is not None:
            if shared.player.guns[
                shared.player.currently_equipped
            ].cooldown.is_cooling_down:
                self.cooldown_indicator.draw()
