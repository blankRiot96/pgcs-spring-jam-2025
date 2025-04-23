import math
import random
import time

import pygame

from src import shared, utils


class BeamTargetingData:
    start_position = pygame.Vector2()
    end_position = pygame.Vector2()


class BeamSegment:
    def __init__(self, angle: float, speed: float):
        self.speed = speed
        self.angle = angle
        self.surface = pygame.Surface((5, 1), pygame.SRCALPHA)
        self.surface.fill("red")
        self.surface = pygame.transform.rotate(self.surface, math.degrees(angle))
        self.position = pygame.Vector2()
        self.alpha = 0
        self.initial_position = pygame.Vector2()
        self.active = True
        self.radius = 70

    def draw(self, position):
        self.position = pygame.Vector2(position) - (
            math.cos(self.angle) * self.radius,
            math.sin(-self.angle) * self.radius,
        )

        self.radius -= 10 * shared.dt
        self.alpha = 400 * (1.0 - (self.radius / 70))
        self.surface.set_alpha(self.alpha)

        if self.radius <= shared.TILE_SIDE / 3:
            self.active = False

        shared.screen.blit(self.surface, shared.camera.transform(self.position))


class BeamImplosion:
    def __init__(self, speed):
        segment_count = 20
        step = math.pi * 2 / segment_count
        self.segments = [BeamSegment(step * i, speed) for i in range(segment_count)]
        self.active = True

    def draw(self, position):
        for segment in self.segments[:]:
            segment.draw(position)
            if not segment.active:
                self.segments.remove(segment)
        self.active = bool(self.segments)


class ChargingAnimation:
    def __init__(self):
        self.speed = 1000
        self.implosions: list[BeamImplosion] = [BeamImplosion(self.speed)]
        self.timer = utils.Timer(0.2)
        self.charged = False
        self.elapsed_time = 0.0
        self.start_time = time.perf_counter()

    def draw(self, position):
        self.elapsed_time = time.perf_counter() - self.start_time
        if self.timer.tick():
            self.implosions.append(BeamImplosion(self.speed))
        for implosion in self.implosions[:]:
            implosion.draw(position)
            if not implosion.active:
                self.implosions.remove(implosion)


class EnergyBeam:
    FADE_DURATION = 0.7
    BEAM_WIDTH = 17.0

    def __init__(self):
        self._active = False
        self.alpha = 255
        self.start_time = time.perf_counter()
        self.first = True

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, state: bool):
        self.start_time = time.perf_counter()
        self._active = state

    def draw(self, start_pos, end_pos):
        if not self._active:
            self.first = True
            return

        if self.first:
            self.start_pos = start_pos
            self.end_pos = utils.move_further(
                pygame.Vector2(end_pos), pygame.Vector2(start_pos)
            )
            self.first = False

        elapsed = time.perf_counter() - self.start_time
        width = EnergyBeam.BEAM_WIDTH * (1 - (elapsed / EnergyBeam.FADE_DURATION))
        pygame.draw.line(
            shared.screen,
            (255, 0, 0),
            shared.camera.transform(self.start_pos),
            shared.camera.transform(self.end_pos),
            width=int(width),
        )

        if width <= 1:
            self._active = False


class Drone:
    SPEED = 20
    BEAM_CHARGE_TIME = 5.0

    def __init__(self, position):
        self.body = pygame.transform.scale_by(
            utils.circle_surf(shared.TILE_SIDE / 4, (150, 150, 150)), 4
        )
        self.eye_color = pygame.Color("white")
        self.eye = utils.circle_surf(shared.TILE_SIDE / 3, self.eye_color)
        self.eye_rect = self.eye.get_rect()
        self.position = pygame.Vector2(position)
        self.rect = self.body.get_rect(topleft=self.position)

        self.tracking = True
        self.charging_animation = ChargingAnimation()
        self.firing = False
        self.fire_start_time = time.perf_counter()

        self.beam = EnergyBeam()

    def update(self):
        player_position = shared.player.collider.pos
        distance_to_player = self.position.distance_to(player_position)

        if self.tracking:
            self.tracking = distance_to_player > 400

        if self.firing:
            self.tracking = False
            if time.perf_counter() - self.fire_start_time > 2.0:
                self.firing = False

        if distance_to_player > 200 and not self.firing:
            self.position.move_towards_ip(player_position, Drone.SPEED * shared.dt)

        self.rect.topleft = self.position

        eye_offset = 10
        angle_to_player = utils.rad_to(self.position, player_position)
        self.eye_rect.center = (
            self.rect.centerx + math.cos(angle_to_player) * eye_offset,
            self.rect.centery + math.sin(angle_to_player) * eye_offset,
        )

        if not self.firing:
            charge_progress = (
                self.charging_animation.elapsed_time / Drone.BEAM_CHARGE_TIME
            )
            charge_progress = 1 - charge_progress
            charge_intensity = int(charge_progress * 255)

            if charge_intensity <= 0:
                self.beam.active = True
                self.fire_start_time = time.perf_counter()
                self.firing = True
                self.charging_animation = ChargingAnimation()
                charge_intensity = 0
                self.tracking = True
                self.eye_color.g, self.eye_color.b = 255, 255
            else:
                self.eye_color.g, self.eye_color.b = charge_intensity, charge_intensity

            self.eye = utils.circle_surf(shared.TILE_SIDE / 3, self.eye_color)

    def draw(self):
        shared.screen.blit(self.body, shared.camera.transform(self.rect))
        shared.screen.blit(
            self.eye,
            shared.camera.transform(
                self.eye_rect.topleft
                + pygame.Vector2(random.randint(1, 3), random.randint(1, 3))
                * (not self.tracking)
                * (not self.firing)
            ),
        )
        self.beam.draw(self.eye_rect.center, shared.player.collider.rect.center)
        if not self.tracking and not self.firing:
            self.charging_animation.draw(self.eye_rect.center)
