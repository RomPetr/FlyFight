"""Scoring and difficulty logic."""

from dataclasses import dataclass

from game import config


@dataclass
class ScoringState:
    score: int = 0
    lives: int = config.PLAYER_START_LIVES
    health: float = 100.0
    level: int = 1
    level_step_score: int = config.LEVEL_UP_BASE_SCORE
    next_level_score: int = config.LEVEL_UP_BASE_SCORE
    run_time_seconds: float = 0.0
    score_multiplier: float = 1.0


def difficulty_multiplier(run_time_seconds: float, score: int) -> float:
    return config.BASE_DIFFICULTY + run_time_seconds * config.TIME_DIFFICULTY_STEP + score * config.SCORE_DIFFICULTY_STEP


def points_for_enemy(enemy_base_points: int, danger_multiplier: float) -> int:
    return int(enemy_base_points * max(1.0, danger_multiplier))


def level_difficulty_multiplier(level: int) -> float:
    return 1.0 + max(0, level - 1) * config.LEVEL_DIFFICULTY_STEP


def process_level_ups(scoring: ScoringState) -> int:
    """Advance level by score threshold, return number of level-ups."""
    leveled = 0
    while scoring.level < config.MAX_LEVEL and scoring.score >= scoring.next_level_score:
        scoring.level += 1
        leveled += 1
        scoring.level_step_score = int(scoring.level_step_score * config.LEVEL_UP_STEP_GROWTH)
        scoring.next_level_score += scoring.level_step_score
    return leveled

