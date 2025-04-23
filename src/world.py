from src import shared, utils
from src.decorations import Decoration, FGDecoration
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
    def __init__(self):
        utils.make_entities_from_tmx("assets/map.tmx", type_factory=ENTITIES)

    def update(self):
        shared.player.update()
        for entity in ENTITIES:
            for obj in entity.objects:
                obj.update()

    def render_entities(self, entities: list[utils.EntityType]):
        for entity in entities:
            for obj in entity.objects:
                obj.draw()

    def draw(self):
        self.render_entities([Tile, Decoration, HittingTarget])
        shared.player.draw()
        self.render_entities([Pistol, Shotgun, HellPit, FGDecoration])
