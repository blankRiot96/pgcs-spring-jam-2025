from enum import Enum, auto


class State(Enum):
    INTRO_STATE = auto()
    LEVEL_SELECTOR = auto()
    GAME = auto()
    GAME_OVER = auto()
