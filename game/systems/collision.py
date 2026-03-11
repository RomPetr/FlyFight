"""Collision and rule handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from game import config
from game.entities.asteroid import Asteroid
from game.entities.bonus import BonusPickup
from game.entities.bullet import Bullet
from game.entities.enemy import EnemyShip
from game.entities.mine import Mine
from game.entities.player import PlayerShip
from game.systems.effects import EffectsSystem
from game.systems.scoring import ScoringState, difficulty_multiplier, points_for_enemy

if TYPE_CHECKING:
    from game.systems.sound import SoundManager


@dataclass
class PlayerBonuses:
    weapon_level: int = 1
    weapon_timer: float = 0.0
    strong_laser_timer: float = 0.0
    speed_timer: float = 0.0
    shield_timer: float = 0.0

    def update(self, dt: float, player: PlayerShip) -> None:
        self.weapon_timer = max(0.0, self.weapon_timer - dt)
        self.strong_laser_timer = max(0.0, self.strong_laser_timer - dt)
        self.speed_timer = max(0.0, self.speed_timer - dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        if self.strong_laser_timer > 0:
            self.weapon_level = 3
        elif self.weapon_timer > 0:
            self.weapon_level = 2
        else:
            self.weapon_level = 1
        player.speed = config.PLAYER_SPEED * (1.25 if self.speed_timer > 0 else 1.0)


def handle_collisions(
    player: PlayerShip,
    bullets: list[Bullet],
    enemies: list[EnemyShip],
    asteroids: list[Asteroid],
    bonuses: list[BonusPickup],
    mines: list[Mine],
    scoring: ScoringState,
    effects: EffectsSystem,
    player_bonuses: PlayerBonuses,
    sound: SoundManager | None = None,
) -> None:
    _resolve_player_bullets(bullets, enemies, asteroids, scoring, effects)
    _resolve_enemy_bullets(bullets, player, scoring, effects, player_bonuses, sound)
    _resolve_direct_collisions(player, enemies, asteroids, mines, scoring, effects, player_bonuses, sound)
    _resolve_pickups(player, bonuses, scoring, player_bonuses, effects, sound)
    _cleanup_offscreen(bullets, enemies, asteroids, bonuses, mines)


def _resolve_player_bullets(
    bullets: list[Bullet],
    enemies: list[EnemyShip],
    asteroids: list[Asteroid],
    scoring: ScoringState,
    effects: EffectsSystem,
) -> None:
    for bullet in [b for b in bullets if b.from_player]:
        # Enemy hits
        for enemy in enemies:
            if bullet.rect.colliderect(enemy.rect):
                enemy.hp -= bullet.damage
                if bullet in bullets:
                    bullets.remove(bullet)
                if enemy.hp <= 0:
                    danger = difficulty_multiplier(scoring.run_time_seconds, scoring.score)
                    gained = points_for_enemy(enemy.point_value, danger) * scoring.score_multiplier
                    scoring.score += int(gained)
                    effects.add_explosion(enemy.rect.centerx, enemy.rect.centery, big=enemy.tier in ("heavy", "elite"))
                    enemies.remove(enemy)
                break
        else:
            # Asteroid hits
            for asteroid in asteroids:
                if bullet.rect.colliderect(asteroid.rect):
                    asteroid.hp -= bullet.damage
                    if bullet in bullets:
                        bullets.remove(bullet)
                    if asteroid.hp <= 0:
                        scoring.score += int(20 * scoring.score_multiplier)
                        effects.add_explosion(asteroid.rect.centerx, asteroid.rect.centery)
                        asteroids.remove(asteroid)
                    break


def _resolve_enemy_bullets(
    bullets: list[Bullet],
    player: PlayerShip,
    scoring: ScoringState,
    effects: EffectsSystem,
    player_bonuses: PlayerBonuses,
    sound: SoundManager | None = None,
) -> None:
    for bullet in [b for b in bullets if not b.from_player]:
        if bullet.rect.colliderect(player.rect):
            if bullet in bullets:
                bullets.remove(bullet)
            _damage_player(player, scoring, effects, player_bonuses, damage_percent=20.0, sound=sound)


def _resolve_direct_collisions(
    player: PlayerShip,
    enemies: list[EnemyShip],
    asteroids: list[Asteroid],
    mines: list[Mine],
    scoring: ScoringState,
    effects: EffectsSystem,
    player_bonuses: PlayerBonuses,
    sound: SoundManager | None = None,
) -> None:
    for enemy in list(enemies):
        if player.rect.colliderect(enemy.rect):
            effects.add_explosion(enemy.rect.centerx, enemy.rect.centery, big=True)
            enemies.remove(enemy)
            enemy_collision_damage = {
                "light": 20.0,
                "medium": 50.0,
                "heavy": 90.0,
                "elite": 90.0,
            }.get(enemy.tier, 20.0)
            _damage_player(player, scoring, effects, player_bonuses, damage_percent=enemy_collision_damage, sound=sound)

    for asteroid in list(asteroids):
        if player.rect.colliderect(asteroid.rect):
            effects.add_explosion(asteroid.rect.centerx, asteroid.rect.centery, mine_style=True)
            asteroids.remove(asteroid)
            asteroid_damage = {
                "small": 20.0,
                "medium": 50.0,
                "large": 90.0,
            }.get(asteroid.size_rank, 20.0)
            _damage_player(player, scoring, effects, player_bonuses, damage_percent=asteroid_damage, sound=sound)

    for mine in list(mines):
        if player.rect.colliderect(mine.rect):
            effects.add_explosion(mine.rect.centerx, mine.rect.centery, big=True, mine_style=True)
            mines.remove(mine)
            _damage_player(
                player,
                scoring,
                effects,
                player_bonuses,
                damage_percent=100.0,
                force_life_loss=True,
                sound=sound,
            )


def _resolve_pickups(
    player: PlayerShip,
    bonuses: list[BonusPickup],
    scoring: ScoringState,
    player_bonuses: PlayerBonuses,
    effects: EffectsSystem,
    sound: SoundManager | None = None,
) -> None:
    for bonus in list(bonuses):
        if not player.rect.colliderect(bonus.rect):
            continue
        bonuses.remove(bonus)
        effects.add_explosion(bonus.rect.centerx, bonus.rect.centery)
        if bonus.bonus_type == "shield":
            if sound:
                sound.play_pickup()
            player_bonuses.shield_timer = 6.0
        elif bonus.bonus_type == "weapon":
            if sound:
                sound.play_weapon_upgrade_pickup()
            player_bonuses.weapon_timer = 7.0
        elif bonus.bonus_type == "strong_laser":
            if sound:
                sound.play_pickup()
            player_bonuses.strong_laser_timer = 9.0
            # Keep base weapon active while strong laser is active.
            player_bonuses.weapon_timer = max(player_bonuses.weapon_timer, 9.0)
        elif bonus.bonus_type == "score":
            if sound:
                sound.play_pickup()
            scoring.score_multiplier = min(2.4, scoring.score_multiplier + 0.25)
        elif bonus.bonus_type == "speed":
            if sound:
                sound.play_pickup()
            player_bonuses.speed_timer = 6.0
        elif bonus.bonus_type == "life":
            if sound:
                sound.play_pickup()
            scoring.lives = min(config.MAX_LIVES, scoring.lives + 1)


def _cleanup_offscreen(
    bullets: list[Bullet],
    enemies: list[EnemyShip],
    asteroids: list[Asteroid],
    bonuses: list[BonusPickup],
    mines: list[Mine],
) -> None:
    bullets[:] = [b for b in bullets if -40 < b.rect.y < config.SCREEN_HEIGHT + 40]
    enemies[:] = [e for e in enemies if e.rect.top <= config.SCREEN_HEIGHT + 60]
    asteroids[:] = [a for a in asteroids if a.rect.top <= config.SCREEN_HEIGHT + 60]
    bonuses[:] = [b for b in bonuses if b.rect.top <= config.SCREEN_HEIGHT + 40]
    mines[:] = [m for m in mines if m.rect.top <= config.SCREEN_HEIGHT + 50]


def _damage_player(
    player: PlayerShip,
    scoring: ScoringState,
    effects: EffectsSystem,
    player_bonuses: PlayerBonuses,
    damage_percent: float,
    force_life_loss: bool = False,
    sound: SoundManager | None = None,
) -> None:
    if player.invulnerable_time > 0.0:
        return
    if player_bonuses.shield_timer > 0.0:
        player_bonuses.shield_timer = max(0.0, player_bonuses.shield_timer - 2.0)
        return
    if force_life_loss:
        scoring.health = 0.0
    else:
        scoring.health = max(0.0, scoring.health - damage_percent)

    if scoring.health > 0.0:
        effects.add_explosion(player.rect.centerx, player.rect.centery, big=False, mine_style=True)
        return

    scoring.lives -= 1
    scoring.health = 100.0
    player.invulnerable_time = config.RESPAWN_INVULN_SECONDS
    effects.add_explosion(player.rect.centerx, player.rect.centery, big=True)
    if sound:
        sound.play_death()

