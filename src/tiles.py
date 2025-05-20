import typing as t


from src import shared, utils


class Tile:
    objects: list[t.Self] = []

    def __init__(self, pos, image):
        self.pos = pos
        self.collider = utils.Collider(pos, (shared.TILE_SIDE, shared.TILE_SIDE))
        Tile.objects.append(self)
        self.image = image
        self.rect = self.collider.rect

    def update(self):
        pass

    def draw(self):
        shared.screen.blit(self.image, shared.camera.transform(self.collider.pos))
