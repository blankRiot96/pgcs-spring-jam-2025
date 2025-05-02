import pygame

from src import shared, utils
from src.decorations import Decoration, FGDecoration, Note
from src.door import HellPit
from src.filth import Filth
from src.gabriel import Gabriel
from src.guns import GunState, Pistol, SawbladeLauncher, Shotgun
from src.hitting_target import HittingTarget
from src.maurice import Maurice
from src.player import Player
from src.soldier import Soldier
from src.spatial import GravityWell, Portal
from src.spawner import EntitySpawner
from src.tiles import Tile
from src.virtue import Virtue

ENTITIES: list[utils.EntityType] = [
    Tile,
    Player,
    HittingTarget,
    Pistol,
    Shotgun,
    SawbladeLauncher,
    HellPit,
    Decoration,
    FGDecoration,
    Filth,
    Maurice,
    Soldier,
    Virtue,
    Gabriel,
]


class World:
    GRADIAL_LAYERS = 20

    def __init__(self):
        shared.pistol_bullets = []
        shared.shotgun_bullets = []
        shared.coins = []
        shared.fireballs = []
        shared.cores = []
        shared.explosions = []
        shared.blood_splatters = []
        shared.sawblades = []
        shared.magnets = []
        utils.make_entities_from_tmx(
            f"assets/map_{shared.level_no}.tmx", type_factory=ENTITIES
        )
        self.get_save_weapons()
        self.make_note_objects()
        self.make_portals()
        self.make_spawners()
        self.make_gravity_wells()
        self.create_hell_gradient()

    def get_save_weapons(self):
        weapons = shared.save_data["weapons"]

        def guip(weapon_name, gun_type):
            if weapon_name not in weapons:
                return

            if gun_type.objects:
                gun_type.objects[0].state = GunState.INVENTORY
            else:
                obj = gun_type(
                    (0, 0),
                    utils.load_image(f"assets/{weapon_name}.png", True, bound=True),
                )
                obj.state = GunState.INVENTORY

        guip("pistol", Pistol)
        guip("shotgun", Shotgun)
        guip("sawblade", SawbladeLauncher)

    def make_portals(self):
        try:
            portals_layer = shared.tmx_map.get_layer_by_name("Portals")
        except ValueError:
            return

        for obj in portals_layer:  # type: ignore
            Portal(
                (obj.x, obj.y),
                obj.image,
                obj.properties["side"],
                obj.properties["sync"],
            )

        for obj1 in Portal.objects:
            for obj2 in Portal.objects:
                if obj1.id == obj2.id and obj1 is not obj2:
                    obj1.other = obj2
                    obj2.other = obj1

    def make_note_objects(self):
        try:
            notes_layer = shared.tmx_map.get_layer_by_name("Notes")
        except ValueError:
            return
        for obj in notes_layer:  # type: ignore
            Note((obj.x, obj.y), obj.image, obj.properties["text"])

    def make_spawners(self):
        try:
            spawner_layer = shared.tmx_map.get_layer_by_name("Spawners")
        except ValueError:
            return

        for map_obj in spawner_layer:  # type: ignore
            spawner = EntitySpawner(
                (map_obj.x, map_obj.y), map_obj.width, map_obj.height
            )

            for entity_type in (Filth, Virtue, Soldier, Maurice):
                for obj in entity_type.objects:
                    if spawner.rect.colliderect(obj.rect):
                        obj.spawner = spawner

    def make_gravity_wells(self):
        try:
            wells_layer = shared.tmx_map.get_layer_by_name("GravityWells")
        except ValueError:
            return

        for obj in wells_layer:  # type: ignore
            GravityWell((obj.x, obj.y), obj.width, obj.height, obj.properties["acc"])

    def create_hell_gradient(self):
        if shared.level_no == shared.BOSS_LEVEL:
            return
        n_layers = World.GRADIAL_LAYERS
        self.hell_gradient = pygame.Surface(
            (
                (shared.tmx_map.width + (n_layers * 2)) * shared.TILE_SIDE,
                (shared.tmx_map.height + (n_layers * 2)) * shared.TILE_SIDE,
            ),
            pygame.SRCALPHA,
        )
        gradial_tile_images = [
            utils.darken_image(
                shared.ENTITY_CLASS_IMAGES["Tile"].copy(), 255 * (i / n_layers)
            )
            for i in range(n_layers)
        ]

        def hawk_tuah(pos, image):
            self.hell_gradient.blit(
                image,
                pygame.Vector2(pos)
                + (
                    n_layers * shared.TILE_SIDE,
                    n_layers * shared.TILE_SIDE,
                ),
            )

        # Left
        for row in range(shared.tmx_map.height):
            for col in range(0, -n_layers, -1):
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[abs(col)],
                )

        # Up
        for col in range(shared.tmx_map.width):
            for row in range(0, -n_layers, -1):
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[abs(row)],
                )

        # Right
        for row in range(shared.tmx_map.height):
            for col in range(shared.tmx_map.width, shared.tmx_map.width + n_layers):
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[abs(col - shared.tmx_map.width)],
                )

        # Down
        for col in range(shared.tmx_map.width):
            for row in range(shared.tmx_map.height, shared.tmx_map.height + n_layers):
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[abs(row - shared.tmx_map.height)],
                )

        # Top-left corner
        for row in range(0, -n_layers, -1):
            for col in range(0, -n_layers, -1):
                d = max(abs(row), abs(col))
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[d],
                )

        # Top-right corner
        for row in range(0, -n_layers, -1):
            for col in range(shared.tmx_map.width, shared.tmx_map.width + n_layers):
                d = max(abs(row), abs(col - shared.tmx_map.width))
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[d],
                )

        # Bottom-left corner
        for row in range(shared.tmx_map.height, shared.tmx_map.height + n_layers):
            for col in range(0, -n_layers, -1):
                d = max(abs(row - shared.tmx_map.height), abs(col))
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[d],
                )

        # Bottom-right corner
        for row in range(shared.tmx_map.height, shared.tmx_map.height + n_layers):
            for col in range(shared.tmx_map.width, shared.tmx_map.width + n_layers):
                d = max(
                    abs(row - shared.tmx_map.height), abs(col - shared.tmx_map.width)
                )
                hawk_tuah(
                    (col * shared.TILE_SIDE, row * shared.TILE_SIDE),
                    gradial_tile_images[d],
                )

    def clear_world(self):
        utils.Collider.all_colliders.clear()
        for entity in ENTITIES + [Note, EntitySpawner, GravityWell, Portal]:
            entity.objects.clear()

    def update(self):
        if not shared.is_world_frozen:
            shared.player.update()
            for entity in ENTITIES + [EntitySpawner, GravityWell, Portal]:
                for obj in entity.objects:
                    obj.update()

            utils.updater(shared.pistol_bullets)
            utils.updater(shared.shotgun_bullets)
            utils.updater(shared.coins)
            utils.updater(shared.fireballs)
            utils.updater(shared.cores)
            utils.updater(shared.explosions)
            utils.updater(shared.blood_splatters)
            utils.updater(shared.sawblades)
            utils.updater(shared.magnets)

        if shared.next_state is not None:
            self.clear_world()

    def render_entities(self, entities: list[utils.EntityType]):
        for entity in entities:
            for obj in entity.objects:
                obj.draw()

    def draw(self):
        if shared.level_no != shared.BOSS_LEVEL:
            shared.screen.blit(
                self.hell_gradient,
                shared.camera.transform(
                    pygame.Vector2(-World.GRADIAL_LAYERS, -World.GRADIAL_LAYERS)
                    * shared.TILE_SIDE
                ),
            )
        self.render_entities([Tile, Decoration, HittingTarget, HellPit])
        shared.player.draw()
        self.render_entities(
            [
                Pistol,
                Shotgun,
                SawbladeLauncher,
                FGDecoration,
                Note,
                Filth,
                Soldier,
                Maurice,
                Virtue,
                Gabriel,
            ]
        )

        utils.drawer(shared.pistol_bullets)
        utils.drawer(shared.shotgun_bullets)
        utils.drawer(shared.coins)
        utils.drawer(shared.fireballs)
        utils.drawer(shared.cores)
        utils.drawer(shared.explosions)
        utils.drawer(shared.blood_splatters)
        utils.drawer(shared.sawblades)
        utils.drawer(shared.magnets)

        shared.player.draw_fist()
        for obj in Portal.objects:
            obj.draw()

        for obj in GravityWell.objects:
            obj.draw()
