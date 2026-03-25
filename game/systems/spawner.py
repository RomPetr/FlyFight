"""Spawn logic for enemies, asteroids, bonuses, and mines."""

import random

from game import config
from game.entities.asteroid import Asteroid
from game.entities.bonus import BonusPickup
from game.entities.enemy import EnemyShip, TIER_ORDER
from game.entities.mine import Mine
from game.systems.scoring import difficulty_multiplier, level_difficulty_multiplier


class SpawnDirector:
    def __init__(self) -> None:
        self.enemy_timer = 0.0
        self.asteroid_timer = 0.0
        self.pickup_timer = 0.0
        self.enemy_rate = config.ENEMY_BASE_RATE
        self.asteroid_rate = config.ASTEROID_BASE_RATE
        self.pickup_rate = config.PICKUP_BASE_RATE

    def update_rates(self, run_time_seconds: float, score: int, level: int) -> None:
        diff = difficulty_multiplier(run_time_seconds, score)
        level_scale = level_difficulty_multiplier(level)
        ease = config.GLOBAL_DIFFICULTY_EASE
        self.enemy_rate = min((config.ENEMY_BASE_RATE + diff * 0.13) * level_scale * ease, config.ENEMY_RATE_CAP)
        self.asteroid_rate = min((config.ASTEROID_BASE_RATE + diff * 0.11) * level_scale * ease, config.ASTEROID_RATE_CAP)
        self.pickup_rate = min((config.PICKUP_BASE_RATE + diff * 0.06) * level_scale * ease, config.PICKUP_RATE_CAP)

    def update(
        self,
        dt: float,
        run_time_seconds: float,
        score: int,
        level: int,
        enemies: list[EnemyShip],
        asteroids: list[Asteroid],
        bonuses: list[BonusPickup],
        mines: list[Mine],
    ) -> None:
        self.update_rates(run_time_seconds, score, level)
        self.enemy_timer += dt
        self.asteroid_timer += dt
        self.pickup_timer += dt

        if self.enemy_timer >= 1.0 / self.enemy_rate and len(enemies) < config.MAX_ENEMIES:
            self.enemy_timer = 0.0
            enemies.append(self._spawn_enemy(run_time_seconds))

        if self.asteroid_timer >= 1.0 / self.asteroid_rate and len(asteroids) < config.MAX_ASTEROIDS:
            self.asteroid_timer = 0.0
            asteroids.append(self._spawn_asteroid())

        if self.pickup_timer >= 1.0 / self.pickup_rate:
            self.pickup_timer = 0.0
            self._spawn_pickup_or_mine(bonuses, mines)

    def _spawn_enemy(self, run_time_seconds: float) -> EnemyShip:
        x = random.randint(25, config.SCREEN_WIDTH - 25)
        t = run_time_seconds
        if t < 45:
            weights = [0.78, 0.2, 0.02, 0.0]
        elif t < 120:
            weights = [0.46, 0.38, 0.13, 0.03]
        else:
            weights = [0.25, 0.42, 0.25, 0.08]
        tier = random.choices(TIER_ORDER, weights=weights, k=1)[0]
        return EnemyShip.create(tier=tier, x_position=x)

    def _spawn_asteroid(self) -> Asteroid:
        x = random.randint(20, config.SCREEN_WIDTH - 20)
        return Asteroid.create(x_position=x)

    def _spawn_pickup_or_mine(self, bonuses: list[BonusPickup], mines: list[Mine]) -> None:
        x = random.randint(20, config.SCREEN_WIDTH - 20)
        roll = random.random()
        if roll < 0.36 and len(mines) < config.MAX_MINES:
            mines.append(Mine.create(x_position=x))
            return
        if len(bonuses) >= config.MAX_PICKUPS:
            return

        # Gifts/bonuses. Extra life is intentionally rare.
        bonus_type = random.choices(
            ["shield", "strong_laser", "speed"],
            # Shield appears less frequently than before.
            weights=[0.24, 0.44, 0.32],
            k=1,
        )[0]
        bonuses.append(BonusPickup.create(bonus_type=bonus_type, x_position=x))

