import pygame

from src import shared, utils
from src.decorations import Decoration, FGDecoration, Note
from src.door import HellPit
from src.guns import Pistol, Shotgun
from src.hitting_target import HittingTarget
from src.player import Player
from src.tiles import Tile

ENTITIES: list[utils.EntityType] = [
    Tile,
    Player,
    HittingTarget,
    Pistol,
    Shotgun,
    HellPit,
    Decoration,
    FGDecoration,
]


class World:
    GRADIAL_LAYERS = 20

    def __init__(self):
        utils.make_entities_from_tmx(
            f"assets/map_{shared.level_no}.tmx", type_factory=ENTITIES
        )
        self.make_note_objects()
        self.create_hell_gradient()

    def make_note_objects(self):
        notes_layer = shared.tmx_map.get_layer_by_name("Notes")
        for obj in notes_layer:  # type: ignore
            Note((obj.x, obj.y), obj.image, obj.properties["text"])

    def create_hell_gradient(self):
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
        for entity in ENTITIES:
            entity.objects.clear()

    def update(self):
        shared.player.update()
        for entity in ENTITIES:
            for obj in entity.objects:
                obj.update()

        if shared.next_state is not None:
            self.clear_world()

    def render_entities(self, entities: list[utils.EntityType]):
        for entity in entities:
            for obj in entity.objects:
                obj.draw()

    def draw(self):
        shared.screen.blit(
            self.hell_gradient,
            shared.camera.transform(
                pygame.Vector2(-World.GRADIAL_LAYERS, -World.GRADIAL_LAYERS)
                * shared.TILE_SIDE
            ),
        )
        self.render_entities([Tile, Decoration, HittingTarget, HellPit])
        shared.player.draw()
        self.render_entities([Pistol, Shotgun, FGDecoration])

        for note in Note.objects:
            note.draw()
