"""Scoring and difficulty logic."""

from dataclasses import dataclass

from game import config


@dataclass
class ScoringState:
    score: int = 0
    lives: int = config.PLAYER_START_LIVES
    health: float = 100.0
    run_time_seconds: float = 0.0
    score_multiplier: float = 1.0


def difficulty_multiplier(run_time_seconds: float, score: int) -> float:
    return config.BASE_DIFFICULTY + run_time_seconds * config.TIME_DIFFICULTY_STEP + score * config.SCORE_DIFFICULTY_STEP


def points_for_enemy(enemy_base_points: int, danger_multiplier: float) -> int:
    return int(enemy_base_points * max(1.0, danger_multiplier))

