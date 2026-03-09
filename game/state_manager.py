"""Game state definitions and helpers."""

from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()

