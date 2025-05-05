import math
import random
import time
import typing as t
from dataclasses import dataclass, field
from enum import Enum, auto

import pygame

from src import shared, utils
from src.blood_splatter import BloodSplatter
from src.fireball import FireBall
from src.tiles import Tile
from src.ui import CoinLineEffect, Flash


class Attack(Enum):
    DROPPING = auto()
    DUAL_SWORD_TOSS = auto()
    FIREBALLS = auto()
    RAIN_OF_SWORDS = auto()


class Spawner:
    def __init__(self) -> None:
        self.activated = True


@dataclass
class RainSword:
    gabriel_center: pygame.Vector2
    pos: pygame.Vector2 = field(init=False)
    rect: pygame.Rect = field(init=False)
    vel_y: float = 0.0
    alive: bool = True

    def __post_init__(self):
        self.pos = pygame.Vector2(
            random.randrange(
                int(self.gabriel_center.x - shared.srect.width / 2),
                int(self.gabriel_center.x + shared.srect.width / 2),
            ),
            self.gabriel_center.y,
        )
        image = utils.load_image("assets/sword.png", True, bound=True)
        self.rect = image.get_rect(center=self.pos)

    def update(self):
        if self.vel_y > shared.MAX_FALL_VELOCITY:
            self.vel_y = shared.MAX_FALL_VELOCITY
        else:
            self.vel_y += shared.WORLD_GRAVITY * shared.dt
        self.pos.y += self.vel_y * shared.dt
        self.rect.centery = self.pos.y

        if self.rect.colliderect(shared.player.collider.rect):
            self.alive = False
            shared.player.health -= 20

        if self.pos.y > (shared.tmx_map.height * shared.TILE_SIDE) + 1200:
            self.alive = False


@dataclass
class RainOfSwordsData:
    swords: list[RainSword] = field(default_factory=list)
    spawn_cooldown: utils.Timer = utils.Timer(0.01)
    image: pygame.Surface = field(init=False)

    def __post_init__(self):
        self.image = utils.load_image("assets/sword.png", True, bound=True)
        self.image = pygame.transform.rotate(self.image, -90)


@dataclass
class DualTossData:
    damage: int

    anchor: pygame.Vector2
    gabriel_rect: pygame.Rect

    sword_1_pos: pygame.Vector2 = field(init=False)
    sword_2_pos: pygame.Vector2 = field(init=False)

    sword_1_target_pos: pygame.Vector2 = field(init=False)
    sword_2_target_pos: pygame.Vector2 = field(init=False)

    sword_1_blit_data: tuple[pygame.Surface, pygame.typing.Point] = field(init=False)
    sword_2_blit_data: tuple[pygame.Surface, pygame.typing.Point] = field(init=False)

    sword_deg: float = 0.0
    phase: int = 1
    damaged_in_phase: bool = False

    def __post_init__(self):
        self.sword_1_pos = self.gabriel_rect.midleft - pygame.Vector2(10, 0)
        self.sword_2_pos = self.gabriel_rect.midright + pygame.Vector2(10, 0)

        dist = self.sword_1_pos.distance_to(self.anchor) + 100
        rad1 = utils.rad_to(self.sword_1_pos, self.anchor)
        rad2 = utils.rad_to(self.sword_2_pos, self.anchor)
        self.sword_1_target_pos = utils.move_towards_rad(self.sword_1_pos, -rad1, dist)
        self.sword_2_target_pos = utils.move_towards_rad(self.sword_2_pos, -rad2, dist)


@dataclass
class DroppingData:
    start: float = field(default_factory=time.perf_counter)
    wait_duration: float = 0.2
    positioned: bool = False
    vel_y: float = 0.0
    damage: int = 100


@dataclass
class FireballData:
    start: float = field(default_factory=time.perf_counter)
    cooldown_between_fireball: float = 0.2
    cooldown_between_streak: float = 1.0

    cooldown: utils.Timer = field(init=False)
    streak_cooldown: utils.CooldownTimer = field(init=False)

    n_fireballs: int = 3
    n: int = 0

    def __post_init__(self):
        self.cooldown = utils.Timer(self.cooldown_between_fireball)
        self.streak_cooldown = utils.CooldownTimer(self.cooldown_between_streak)


class Gabriel:
    SPEED = 1.5

    objects: list[t.Self] = []
    spawner = Spawner()

    dropping_data: DroppingData
    fireball_data: FireballData
    dual_toss_data: DualTossData
    rain_of_swords_data: RainOfSwordsData

    def __init__(self, pos, image: pygame.Surface) -> None:
        Gabriel.objects.append(self)
        self.pos = pygame.Vector2(pos)
        self.image = utils.load_image("assets/gabriel2.png", True, bound=True)
        self.enraged_image = utils.load_image(
            "assets/gabriel_enraged.png", True, bound=True
        )
        dummy_rect = pygame.Rect(self.pos, (16, 16))
        self.rect = self.image.get_rect(midbottom=dummy_rect.midbottom)
        self.health = 10_000
        self.sword = utils.load_image("assets/sword.png", True, bound=True)
        self.sway_rad = random.randint(-90, 90)

        self.enraged = False
        self.move_rng_timer = utils.Timer(5.0)
        self.attack_rng_timer = utils.Timer(3.0)

    def on_bullet_collide(self, bullet):
        self.health -= bullet.damage
        bullet.alive = False

        if bullet.coin_history:
            points = [shared.player.collider.pos] + bullet.coin_history + [self.pos]
            shared.fx_manager.coin_lines.append(CoinLineEffect(points))
            shared.fx_manager.flashes.append(Flash())

    def handle_damage(self):
        for bullet in shared.shotgun_bullets + shared.pistol_bullets:
            if self.rect.colliderect(bullet.collider_rect):
                self.on_bullet_collide(bullet)

        for blade in shared.sawblades:
            if blade.rect.colliderect(self.rect):
                self.health -= blade.damage

        for fireball in shared.fireballs:
            if not fireball.boosted:
                continue

            if fireball.rect.colliderect(self.rect):
                self.health -= fireball.DAMAGE
                fireball.alive = False

        if self.health <= 5000:
            self.enraged = True

        if self.health <= 0:
            try:
                Gabriel.objects.remove(self)
                shared.blood_splatters.append(BloodSplatter(self.rect.center, 100))
            except ValueError:
                pass

    def rng_movement(self):
        if self.move_rng_timer.tick():
            self.sway_rad = random.randint(-90, 90)

    def move(self):
        if self.attack not in (Attack.DROPPING, Attack.RAIN_OF_SWORDS):
            self.pos.move_towards_ip(
                shared.player.collider.pos, Gabriel.SPEED * shared.dt
            )
            self.pos = utils.move_towards_rad(
                self.pos, self.sway_rad, Gabriel.SPEED * shared.dt
            )
        self.rect.topleft = self.pos

    def rng_attack(self):
        options = [Attack.DROPPING, Attack.DUAL_SWORD_TOSS, Attack.FIREBALLS]
        if self.enraged:
            options.append(Attack.RAIN_OF_SWORDS)

        self.attack = random.choice(options)
        # self.attack = Attack.RAIN_OF_SWORDS

        if self.attack == Attack.DROPPING:
            if self.enraged:
                self.dropping_data = DroppingData(wait_duration=0.1, damage=200)
            else:
                self.dropping_data = DroppingData()
        elif self.attack == Attack.FIREBALLS:
            if self.enraged:
                self.fireball_data = FireballData(
                    cooldown_between_fireball=0.1,
                    cooldown_between_streak=0.7,
                    n_fireballs=5,
                )
            else:
                self.fireball_data = FireballData()
        elif self.attack == Attack.DUAL_SWORD_TOSS:
            if self.enraged:
                self.dual_toss_data = DualTossData(
                    500, shared.player.collider.pos.copy(), self.rect.copy()
                )
            else:
                self.dual_toss_data = DualTossData(
                    300, shared.player.collider.pos.copy(), self.rect.copy()
                )
        elif self.attack == Attack.RAIN_OF_SWORDS:
            self.rain_of_swords_data = RainOfSwordsData()
            self.pos.y = 250

    def layered_rng_attack(self):
        if not self.attack_rng_timer.tick() or self.attack in (
            Attack.DROPPING,
            Attack.DUAL_SWORD_TOSS,
        ):
            return

        self.attack_rng_timer.time_to_pass = random.uniform(3.0, 7.0)
        self.rng_attack()

    def attack_dropping(self):
        diff = time.perf_counter() - self.dropping_data.start
        acc = 60 if self.enraged else 30

        if (
            diff < self.dropping_data.wait_duration
            and not self.dropping_data.positioned
        ):
            self.rect.centerx = shared.player.collider.rect.centerx
            self.pos.x = self.rect.x
            self.pos.y = shared.player.collider.pos.y - (16 * 7)
            self.rect.topleft = self.pos
            self.dropping_data.positioned = True
        elif diff >= self.dropping_data.wait_duration:
            self.dropping_data.vel_y += acc * shared.dt
            self.pos.y += self.dropping_data.vel_y * shared.dt

            hit_tiles = False
            for tile in Tile.objects:
                if tile.rect.colliderect(self.rect):
                    hit_tiles = True
                    break

            if self.rect.colliderect(shared.player.collider.rect):
                shared.player.health -= self.dropping_data.damage
                self.rng_attack()
            elif hit_tiles:
                self.rng_attack()

    def dual_toss_phase_1(self):
        sword_speed = 50.0
        self.dual_toss_data.sword_1_pos.move_towards_ip(
            self.dual_toss_data.sword_1_target_pos, sword_speed * shared.dt
        )
        self.dual_toss_data.sword_2_pos.move_towards_ip(
            self.dual_toss_data.sword_2_target_pos, sword_speed * shared.dt
        )

        if self.dual_toss_data.sword_1_pos == self.dual_toss_data.sword_1_target_pos:
            self.dual_toss_data.phase = 2
            self.dual_toss_data.damaged_in_phase = False

    def dual_toss_phase_2(self):
        sword_speed = 20.0

        self.dual_toss_data.sword_1_pos.move_towards_ip(
            self.dual_toss_data.sword_2_target_pos, sword_speed * shared.dt
        )
        self.dual_toss_data.sword_2_pos.move_towards_ip(
            self.dual_toss_data.sword_1_target_pos, sword_speed * shared.dt
        )

        if self.dual_toss_data.sword_1_pos == self.dual_toss_data.sword_2_target_pos:
            self.dual_toss_data.phase = 3
            self.dual_toss_data.damaged_in_phase = False

    def dual_toss_phase_3(self):
        sword_speed = 30.0

        self.dual_toss_data.sword_1_pos.move_towards_ip(
            self.rect.midright, sword_speed * shared.dt
        )
        self.dual_toss_data.sword_2_pos.move_towards_ip(
            self.rect.midleft, sword_speed * shared.dt
        )

        if self.dual_toss_data.sword_1_pos == pygame.Vector2(self.rect.midright):
            self.rng_attack()

    def attack_dual_sword_toss(self):
        if self.dual_toss_data.phase == 1:
            self.dual_toss_phase_1()
        elif self.dual_toss_data.phase == 2:
            self.dual_toss_phase_2()
        elif self.dual_toss_data.phase == 3:
            self.dual_toss_phase_3()

        self.dual_toss_data.sword_deg += 200 * shared.dt
        self.dual_toss_data.sword_deg %= 360

        sword_1_image = pygame.transform.rotate(
            self.sword, self.dual_toss_data.sword_deg
        )
        sword_1_rect = sword_1_image.get_rect(center=self.dual_toss_data.sword_1_pos)
        sword_2_image = pygame.transform.rotate(
            self.sword, -self.dual_toss_data.sword_deg
        )
        sword_2_rect = sword_2_image.get_rect(center=self.dual_toss_data.sword_2_pos)

        colliding = sword_1_rect.colliderect(
            shared.player.collider.rect
        ) or sword_2_rect.colliderect(shared.player.collider.rect)
        if colliding and not self.dual_toss_data.damaged_in_phase:
            shared.player.health -= self.dual_toss_data.damage
            self.dual_toss_data.damaged_in_phase = True

        self.dual_toss_data.sword_1_blit_data = (
            sword_1_image,
            shared.camera.transform(sword_1_rect),
        )

        self.dual_toss_data.sword_2_blit_data = (
            sword_2_image,
            shared.camera.transform(sword_2_rect),
        )

    def attack_fireballs(self):
        self.fireball_data.streak_cooldown.update()

        if self.fireball_data.streak_cooldown.is_cooling_down:
            return

        if not self.fireball_data.cooldown.tick():
            return

        shared.fireballs.append(
            FireBall(
                self.rect.center,
                -utils.rad_to(
                    pygame.Vector2(self.rect.center),
                    pygame.Vector2(shared.player.collider.rect.center),
                ),
                100.0,
            )
        )
        self.fireball_data.n += 1

        if self.fireball_data.n >= 3:
            self.fireball_data.streak_cooldown.start()
            self.fireball_data.n = 0

    def attack_rain_of_swords(self):
        if self.rain_of_swords_data.spawn_cooldown.tick():
            self.rain_of_swords_data.swords.append(
                RainSword(pygame.Vector2(self.rect.center))
            )

        for sword in self.rain_of_swords_data.swords[:]:
            sword.update()

            if not sword.alive:
                self.rain_of_swords_data.swords.remove(sword)

    def on_attack(self):
        if self.attack == Attack.DROPPING:
            self.attack_dropping()
        elif self.attack == Attack.DUAL_SWORD_TOSS:
            self.attack_dual_sword_toss()
        elif self.attack == Attack.FIREBALLS:
            self.attack_fireballs()
        elif self.attack == Attack.RAIN_OF_SWORDS:
            self.attack_rain_of_swords()

    def update(self):
        self.rng_movement()
        self.move()
        self.layered_rng_attack()
        self.on_attack()
        self.handle_damage()

    def draw(self):
        if self.enraged:
            shared.screen.blit(self.enraged_image, shared.camera.transform(self.rect))
        else:
            shared.screen.blit(self.image, shared.camera.transform(self.rect))

        if self.attack == Attack.DUAL_SWORD_TOSS and hasattr(
            self.dual_toss_data, "sword_1_blit_data"
        ):
            shared.screen.blit(*self.dual_toss_data.sword_1_blit_data)
            shared.screen.blit(*self.dual_toss_data.sword_2_blit_data)
        elif self.attack == Attack.RAIN_OF_SWORDS:
            for sword in self.rain_of_swords_data.swords:
                shared.screen.blit(
                    self.rain_of_swords_data.image, shared.camera.transform(sword.rect)
                )
