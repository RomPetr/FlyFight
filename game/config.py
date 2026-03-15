"""Central configuration for FlyFight."""

from pathlib import Path

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TITLE = "FlyFight - Space Shooter"

# Colors
COLOR_BG = (5, 9, 26)
COLOR_PLAYER = (80, 220, 255)
COLOR_ASTEROID = (130, 130, 130)
COLOR_MINE = (255, 60, 80)
COLOR_BONUS = (80, 255, 120)
COLOR_TEXT = (235, 245, 255)
COLOR_WARNING = (255, 110, 110)

# Gameplay
PLAYER_SPEED = 360.0
BULLET_SPEED = 650.0
BULLET_COOLDOWN = 0.18
PLAYER_START_LIVES = 3
MAX_LIVES = 5
RESPAWN_INVULN_SECONDS = 1.2

# Score and progression
BASE_DIFFICULTY = 1.0
TIME_DIFFICULTY_STEP = 0.03  # every second
SCORE_DIFFICULTY_STEP = 0.00045

ENEMY_TIER_CONFIG = {
    # Clear visual rank spacing for enemy hull size.
    "light": {"hp": 1, "speed": 120.0, "points": 80, "size": 26, "shot_cd": 1.8},
    "medium": {"hp": 2, "speed": 95.0, "points": 180, "size": 34, "shot_cd": 1.5},
    "heavy": {"hp": 3, "speed": 75.0, "points": 380, "size": 42, "shot_cd": 1.3},
    "elite": {"hp": 3, "speed": 65.0, "points": 700, "size": 58, "shot_cd": 1.1},
}

# Spawn pacing
ASTEROID_BASE_RATE = 0.75
ENEMY_BASE_RATE = 0.65
PICKUP_BASE_RATE = 0.35

# Level progression
MAX_LEVEL = 5
LEVEL_UP_BASE_SCORE = 700
LEVEL_UP_STEP_GROWTH = 1.2
LEVEL_DIFFICULTY_STEP = 0.2
GLOBAL_DIFFICULTY_EASE = 0.82

# Audio
SOUNDS_DIR = Path("SoundExamples")

# Save system
SAVE_DIR = Path("save_data")
CHECKPOINT_FILE = SAVE_DIR / "checkpoint.json"
AUDIO_SETTINGS_FILE = SAVE_DIR / "audio_settings.json"
AUTOSAVE_SECONDS = 14.0
AUTOSAVE_SCORE_STEP = 900
