"""Centralized sprite/asset loader with caching and graceful fallback.

Priority order for each entity:
  1. game/assets/images/  (user-supplied, converted from IMAGES/)
  2. SpaceShooterRedux/PNG/  (bundled sprite pack)
  3. Primitive drawing fallback in each entity's draw()

If a file cannot be found or pygame is not yet initialised, functions return
None and callers fall back to the next option or primitive drawing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pygame

# Project root is two levels up from this file (game/assets.py → game/ → project root)
_ROOT = Path(__file__).parent.parent
_PNG = _ROOT / "SpaceShooterRedux" / "PNG"
_BG = _ROOT / "SpaceShooterRedux" / "Backgrounds"
_IMAGES = _ROOT / "game" / "assets" / "images"
_USER_IMAGES = _ROOT / "IMAGES"

# Simple path+size+flip key → Surface (or None on failure)
_cache: dict[str, Optional[pygame.Surface]] = {}


def _load(
    path: Path,
    size: tuple[int, int] | None = None,
    flip_v: bool = False,
) -> Optional[pygame.Surface]:
    """Load, optionally scale/flip, and cache a sprite surface."""
    key = f"{path}|{size}|{flip_v}"
    if key in _cache:
        return _cache[key]

    try:
        if not path.exists():
            _cache[key] = None
            return None
        img = pygame.image.load(str(path)).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        if flip_v:
            img = pygame.transform.flip(img, False, True)
        _cache[key] = img
    except Exception:
        _cache[key] = None

    return _cache[key]


def _load_from_user_layers(
    relative_name: str,
    size: tuple[int, int] | None = None,
    flip_v: bool = False,
) -> Optional[pygame.Surface]:
    """Try game/assets/images first, then IMAGES root."""
    return _load(_IMAGES / relative_name, size, flip_v) or _load(_USER_IMAGES / relative_name, size, flip_v)


def _first_existing_by_patterns(patterns: list[str]) -> Path | None:
    for pattern in patterns:
        for folder in (_IMAGES, _USER_IMAGES):
            matches = sorted(folder.glob(pattern))
            if matches:
                return matches[0]
    return None


# ---------------------------------------------------------------------------
# Player ship
# ---------------------------------------------------------------------------

def get_player_ship(width: int, height: int) -> Optional[pygame.Surface]:
    return (
        _load_from_user_layers("ship.png", (width, height))
        or _load(_PNG / "playerShip1_blue.png", (width, height))
    )


# ---------------------------------------------------------------------------
# Enemy ships
# ---------------------------------------------------------------------------

_ENEMY_USER_FILES = {
    "light":  "weak_enemy.png",
    "medium": "medium_enemy.png",
    "heavy":  "strong_enemy.png",
    "elite":  "elite_enemy.png",
}

_ENEMY_SRX_FILES = {
    "light":  "enemyBlue1.png",
    "medium": "enemyGreen1.png",
    "heavy":  "enemyRed1.png",
    "elite":  "enemyBlack1.png",
}


def get_enemy_ship(tier: str, size: int) -> Optional[pygame.Surface]:
    user_file = _ENEMY_USER_FILES.get(tier)
    srx_file = _ENEMY_SRX_FILES.get(tier, "enemyBlue1.png")
    return (
        (user_file and _load_from_user_layers(user_file, (size, size)))
        or _load(_PNG / "Enemies" / srx_file, (size, size))
    )


# ---------------------------------------------------------------------------
# Meteors / asteroids
# ---------------------------------------------------------------------------

_METEOR_POOLS: dict[str, list[str]] = {
    "big": [
        "meteorBrown_big1.png", "meteorBrown_big2.png",
        "meteorBrown_big3.png", "meteorBrown_big4.png",
        "meteorGrey_big1.png", "meteorGrey_big2.png",
    ],
    "med": [
        "meteorBrown_med1.png", "meteorBrown_med3.png",
        "meteorGrey_med1.png", "meteorGrey_med2.png",
    ],
    "small": [
        "meteorBrown_small1.png", "meteorBrown_small2.png",
        "meteorGrey_small1.png", "meteorGrey_small2.png",
    ],
    "tiny": [
        "meteorBrown_tiny1.png", "meteorBrown_tiny2.png",
        "meteorGrey_tiny1.png", "meteorGrey_tiny2.png",
    ],
}


def pick_meteor_name(size: int) -> str:
    """Return a meteor filename appropriate for the given asteroid size."""
    import random

    # Prefer explicit user-provided 3-rank meteor sprites.
    if size >= 52:
        preferred = "meteor_large.png"
    elif size >= 36:
        preferred = "meteor_medium.png"
    else:
        preferred = "meteor_small.png"

    if (_IMAGES / preferred).exists():
        return preferred
    if (_USER_IMAGES / preferred).exists():
        return preferred

    # Fallback to legacy SpaceShooterRedux meteor variants.
    if size >= 45:
        pool = _METEOR_POOLS["big"]
    elif size >= 36:
        pool = _METEOR_POOLS["med"]
    elif size >= 26:
        pool = _METEOR_POOLS["small"]
    else:
        pool = _METEOR_POOLS["tiny"]
    return random.choice(pool)


def get_meteor(filename: str, width: int, height: int) -> Optional[pygame.Surface]:
    return (
        _load_from_user_layers(filename, (width, height))
        or _load_from_user_layers("meteors.png", (width, height))
        or _load(_PNG / "Meteors" / filename, (width, height))
    )


# ---------------------------------------------------------------------------
# Lasers / bullets
# ---------------------------------------------------------------------------

def get_player_laser(width: int, height: int) -> Optional[pygame.Surface]:
    return (
        _load_from_user_layers("rockets.png", (width, height))
        or _load(_PNG / "Lasers" / "laserBlue01.png", (width, height))
    )


def get_enemy_laser(width: int, height: int) -> Optional[pygame.Surface]:
    # laserRed01 points up in the asset; flip so it points downward for enemies
    return _load(_PNG / "Lasers" / "laserRed01.png", (width, height), flip_v=True)


# ---------------------------------------------------------------------------
# Bonus pickups
# ---------------------------------------------------------------------------

_BONUS_FILES = {
    "shield": "powerupBlue_shield.png",
    "weapon": "powerupYellow_bolt.png",
    "strong_laser": "gift_strong_laser.png",
    "score": "powerupGreen_star.png",
    "speed": "powerupBlue_bolt.png",
    "life": "powerupRed_star.png",
}


def get_bonus(bonus_type: str, width: int, height: int) -> Optional[pygame.Surface]:
    # User-provided gifts from IMAGES folder (with long localized names)
    special_patterns = {
        "shield": ["gpt-image-1.5_1*"],
        "weapon": ["gpt-image-1.5_2*"],
        "strong_laser": ["gpt-image-1.5_2*"],
        "speed": ["gpt-image-1.5_3*"],
    }
    patterns = special_patterns.get(bonus_type)
    if patterns:
        candidate = _first_existing_by_patterns(patterns)
        if candidate:
            sprite = _load(candidate, (width, height))
            if sprite is not None:
                return sprite

    filename = _BONUS_FILES.get(bonus_type)
    if not filename:
        return None
    return (
        _load_from_user_layers(filename, (width, height))
        or _load(_PNG / "Power-ups" / filename, (width, height))
    )


# ---------------------------------------------------------------------------
# Mine
# ---------------------------------------------------------------------------

def get_mine(width: int, height: int) -> Optional[pygame.Surface]:
    return _load_from_user_layers("mine1.png", (width, height))


# ---------------------------------------------------------------------------
# Explosion overlays
# ---------------------------------------------------------------------------

def get_explosion(name: str, width: int, height: int) -> Optional[pygame.Surface]:
    """name is 'explosion1' or 'explosion2'."""
    return _load_from_user_layers(f"{name}.png", (width, height)) or _load_from_user_layers(f"{name}.jpg", (width, height))


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

def get_background(width: int, height: int) -> Optional[pygame.Surface]:
    return _load(_USER_IMAGES / "bkgd_0.png", (width, height)) or _load(_BG / "darkPurple.png", (width, height))
