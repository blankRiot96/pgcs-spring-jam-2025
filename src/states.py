import typing as t

from src import shared
from src.enums import State
from src.game_over_state import GameOverState
from src.game_state import GameState
from src.intro_state import IntroState
from src.level_state import LevelState
from src.win_state import WinState


class StateLike(t.Protocol):
    def update(self): ...

    def draw(self): ...


class StateManager:
    def __init__(self) -> None:
        self.state_dict: dict[State, t.Type[StateLike]] = {
            State.INTRO_STATE: IntroState,
            State.LEVEL_SELECTOR: LevelState,
            State.GAME: GameState,
            State.GAME_OVER: GameOverState,
            State.WIN: WinState,
        }

        shared.next_state = State.INTRO_STATE
        self.set_state()

    def set_state(self):
        self.state_obj: StateLike = self.state_dict.get(shared.next_state)()  # type: ignore
        shared.next_state = None

    def update(self):
        self.state_obj.update()
        if shared.next_state is not None:
            self.set_state()

    def draw(self):
        self.state_obj.draw()
