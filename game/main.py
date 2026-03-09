"""FlyFight 2D Space Shooter entry point."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import pygame

from game import assets, config
from game.entities.asteroid import Asteroid
from game.entities.bonus import BonusPickup
from game.entities.bullet import Bullet
from game.entities.enemy import EnemyShip
from game.entities.mine import Mine
from game.entities.player import PlayerShip
from game.save.checkpoint import has_checkpoint, load_checkpoint, save_checkpoint
from game.state_manager import GameState
from game.systems.collision import PlayerBonuses, handle_collisions
from game.systems.effects import EffectsSystem
from game.systems.scoring import ScoringState, difficulty_multiplier
from game.systems.sound import SoundManager
from game.systems.spawner import SpawnDirector
from game.ui.hud import draw_audio_toggles, draw_hud, draw_ship_health_bar


@dataclass
class GameSession:
    player: PlayerShip
    bullets: list[Bullet]
    enemies: list[EnemyShip]
    asteroids: list[Asteroid]
    bonuses: list[BonusPickup]
    mines: list[Mine]
    scoring: ScoringState
    player_bonuses: PlayerBonuses
    effects: EffectsSystem
    spawner: SpawnDirector
    autosave_timer: float = 0.0
    autosave_last_score: int = 0


def new_session() -> GameSession:
    return GameSession(
        player=PlayerShip.create(),
        bullets=[],
        enemies=[],
        asteroids=[],
        bonuses=[],
        mines=[],
        scoring=ScoringState(),
        player_bonuses=PlayerBonuses(),
        effects=EffectsSystem(),
        spawner=SpawnDirector(),
    )


def serialize_session(session: GameSession) -> dict[str, Any]:
    return {
        "player": {
            "x": session.player.rect.x,
            "y": session.player.rect.y,
            "invulnerable_time": session.player.invulnerable_time,
        },
        "scoring": {
            "score": session.scoring.score,
            "lives": session.scoring.lives,
            "health": session.scoring.health,
            "run_time_seconds": session.scoring.run_time_seconds,
            "score_multiplier": session.scoring.score_multiplier,
        },
        "player_bonuses": {
            "weapon_timer": session.player_bonuses.weapon_timer,
            "strong_laser_timer": session.player_bonuses.strong_laser_timer,
            "speed_timer": session.player_bonuses.speed_timer,
            "shield_timer": session.player_bonuses.shield_timer,
        },
        "entities": {
            "bullets": [
                {
                    "x": b.rect.x,
                    "y": b.rect.y,
                    "w": b.rect.width,
                    "h": b.rect.height,
                    "vy": b.velocity_y,
                    "from_player": b.from_player,
                    "damage": b.damage,
                }
                for b in session.bullets
            ],
            "enemies": [
                {
                    "tier": e.tier,
                    "x": e.rect.x,
                    "y": e.rect.y,
                    "hp": e.hp,
                    "shot_timer": e.shot_timer,
                }
                for e in session.enemies
            ],
            "asteroids": [
                {"x": a.rect.x, "y": a.rect.y, "w": a.rect.width, "h": a.rect.height, "speed": a.speed, "hp": a.hp}
                for a in session.asteroids
            ],
            "bonuses": [{"type": p.bonus_type, "x": p.rect.x, "y": p.rect.y} for p in session.bonuses],
            "mines": [{"x": m.rect.x, "y": m.rect.y} for m in session.mines],
        },
        "spawner": {
            "enemy_timer": session.spawner.enemy_timer,
            "asteroid_timer": session.spawner.asteroid_timer,
            "pickup_timer": session.spawner.pickup_timer,
        },
        "autosave_last_score": session.autosave_last_score,
    }


def load_session(payload: dict[str, Any]) -> GameSession:
    session = new_session()

    player_data = payload.get("player", {})
    scoring_data = payload.get("scoring", {})
    bonus_data = payload.get("player_bonuses", {})
    entities = payload.get("entities", {})
    spawner_data = payload.get("spawner", {})

    session.player.rect.x = int(player_data.get("x", session.player.rect.x))
    session.player.rect.y = int(player_data.get("y", session.player.rect.y))
    session.player.invulnerable_time = float(player_data.get("invulnerable_time", 0.0))

    session.scoring.score = int(scoring_data.get("score", 0))
    session.scoring.lives = int(scoring_data.get("lives", config.PLAYER_START_LIVES))
    session.scoring.health = float(scoring_data.get("health", 100.0))
    session.scoring.run_time_seconds = float(scoring_data.get("run_time_seconds", 0.0))
    session.scoring.score_multiplier = float(scoring_data.get("score_multiplier", 1.0))

    session.player_bonuses.weapon_timer = float(bonus_data.get("weapon_timer", 0.0))
    session.player_bonuses.strong_laser_timer = float(bonus_data.get("strong_laser_timer", 0.0))
    session.player_bonuses.speed_timer = float(bonus_data.get("speed_timer", 0.0))
    session.player_bonuses.shield_timer = float(bonus_data.get("shield_timer", 0.0))

    for b in entities.get("bullets", []):
        rect = pygame.Rect(int(b["x"]), int(b["y"]), int(b["w"]), int(b["h"]))
        session.bullets.append(
            Bullet(
                rect=rect,
                velocity_y=float(b["vy"]),
                from_player=bool(b["from_player"]),
                damage=int(b.get("damage", 1)),
            )
        )
    for e in entities.get("enemies", []):
        enemy = EnemyShip.create(str(e["tier"]), int(e["x"]))
        enemy.rect.y = int(e["y"])
        enemy.hp = int(e["hp"])
        enemy.shot_timer = float(e.get("shot_timer", enemy.shot_cd))
        session.enemies.append(enemy)
    for a in entities.get("asteroids", []):
        rect = pygame.Rect(int(a["x"]), int(a["y"]), int(a["w"]), int(a["h"]))
        session.asteroids.append(Asteroid(rect=rect, speed=float(a["speed"]), hp=int(a["hp"])))
    for p in entities.get("bonuses", []):
        bonus = BonusPickup.create(str(p["type"]), int(p["x"]))
        bonus.rect.y = int(p["y"])
        session.bonuses.append(bonus)
    for m in entities.get("mines", []):
        mine = Mine.create(int(m["x"]))
        mine.rect.y = int(m["y"])
        session.mines.append(mine)

    session.spawner.enemy_timer = float(spawner_data.get("enemy_timer", 0.0))
    session.spawner.asteroid_timer = float(spawner_data.get("asteroid_timer", 0.0))
    session.spawner.pickup_timer = float(spawner_data.get("pickup_timer", 0.0))
    session.autosave_last_score = int(payload.get("autosave_last_score", session.scoring.score))
    return session


def draw_scene(
    surface: pygame.Surface,
    session: GameSession,
    stars: list[tuple[int, int, int]],
    offset: tuple[int, int],
    bg: pygame.Surface | None = None,
) -> None:
    scene = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    if bg is not None:
        scene.blit(bg, (0, 0))
    else:
        scene.fill(config.COLOR_BG)

    for sx, sy, size in stars:
        pygame.draw.circle(scene, (200, 210, 255), (sx, sy), size)

    for asteroid in session.asteroids:
        asteroid.draw(scene)
    for mine in session.mines:
        mine.draw(scene)
    for bonus in session.bonuses:
        bonus.draw(scene)
    for enemy in session.enemies:
        enemy.draw(scene)
    for bullet in session.bullets:
        bullet.draw(scene)
    session.player.draw(scene)
    draw_ship_health_bar(scene, session.player.rect, session.scoring.health)
    session.effects.draw(scene)

    surface.blit(scene, offset)


def save_if_needed(session: GameSession) -> None:
    score_trigger = session.scoring.score - session.autosave_last_score >= config.AUTOSAVE_SCORE_STEP
    time_trigger = session.autosave_timer >= config.AUTOSAVE_SECONDS
    if not (score_trigger or time_trigger):
        return

    save_checkpoint(serialize_session(session))
    session.autosave_timer = 0.0
    session.autosave_last_score = session.scoring.score


def get_audio_toggle_rects() -> tuple[pygame.Rect, pygame.Rect]:
    music_rect = pygame.Rect(config.SCREEN_WIDTH - 236, 78, 108, 34)
    sound_rect = pygame.Rect(config.SCREEN_WIDTH - 118, 78, 108, 34)
    return music_rect, sound_rect


def run() -> None:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    sound = SoundManager()
    pygame.display.set_caption(config.TITLE)
    screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("consolas", 26)
    small_font = pygame.font.SysFont("consolas", 18)
    menu_font = pygame.font.SysFont("consolas", 32)

    background = assets.get_background(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

    state = GameState.MENU
    session = new_session()

    stars = [(random.randint(0, config.SCREEN_WIDTH), random.randint(0, config.SCREEN_HEIGHT), random.randint(1, 2)) for _ in range(120)]

    running = True
    while running:
        dt = min(0.033, clock.tick(config.FPS) / 1000.0)
        music_rect, sound_rect = get_audio_toggle_rects()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    sound.toggle_music(should_play_now=(state == GameState.PLAYING))
                elif event.key == pygame.K_F2:
                    sound.toggle_sfx()
                if event.key == pygame.K_ESCAPE:
                    if state == GameState.PLAYING:
                        state = GameState.PAUSED
                        sound.pause_music()
                    elif state == GameState.PAUSED:
                        state = GameState.PLAYING
                        sound.resume_music()
                    elif state in (GameState.MENU, GameState.GAME_OVER):
                        running = False
                if state == GameState.MENU and event.key == pygame.K_n:
                    session = new_session()
                    state = GameState.PLAYING
                    sound.start_music()
                if state == GameState.MENU and event.key == pygame.K_c and has_checkpoint():
                    payload = load_checkpoint()
                    if payload:
                        session = load_session(payload)
                        state = GameState.PLAYING
                        sound.start_music()
                if state == GameState.GAME_OVER and event.key == pygame.K_r:
                    session = new_session()
                    state = GameState.PLAYING
                    sound.start_music()
                if event.key == pygame.K_p and state == GameState.PLAYING:
                    state = GameState.PAUSED
                    sound.pause_music()
                elif event.key == pygame.K_p and state == GameState.PAUSED:
                    state = GameState.PLAYING
                    sound.resume_music()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                if music_rect.collidepoint(mouse_pos):
                    sound.toggle_music(should_play_now=(state == GameState.PLAYING))
                elif sound_rect.collidepoint(mouse_pos):
                    sound.toggle_sfx()

        pressed = pygame.key.get_pressed()

        if state == GameState.PLAYING:
            session.scoring.run_time_seconds += dt
            session.autosave_timer += dt
            session.player_bonuses.update(dt, session.player)
            session.player.update(dt, pressed)
            session.scoring.score_multiplier = max(1.0, session.scoring.score_multiplier - dt * 0.02)

            player_shot = session.player.try_shoot(pressed)
            if player_shot:
                if session.player_bonuses.weapon_level >= 3:
                    player_shot.damage = 3
                    player_shot.rect.width = 10
                    player_shot.rect.height = 26
                    player_shot.rect.centerx = session.player.rect.centerx
                    player_shot.rect.bottom = session.player.rect.top
                sound.play_shoot()
                session.bullets.append(player_shot)
                if session.player_bonuses.weapon_level > 1:
                    side_damage = 2 if session.player_bonuses.weapon_level >= 3 else 1
                    side_h = 20 if session.player_bonuses.weapon_level >= 3 else 16
                    side_w = 8 if session.player_bonuses.weapon_level >= 3 else 6
                    left = Bullet(
                        pygame.Rect(player_shot.rect.x - 12, player_shot.rect.y + 8, side_w, side_h),
                        -config.BULLET_SPEED,
                        True,
                        damage=side_damage,
                    )
                    right = Bullet(
                        pygame.Rect(player_shot.rect.x + 12, player_shot.rect.y + 8, side_w, side_h),
                        -config.BULLET_SPEED,
                        True,
                        damage=side_damage,
                    )
                    session.bullets.extend([left, right])

            session.spawner.update(
                dt=dt,
                run_time_seconds=session.scoring.run_time_seconds,
                score=session.scoring.score,
                enemies=session.enemies,
                asteroids=session.asteroids,
                bonuses=session.bonuses,
                mines=session.mines,
            )

            for enemy in session.enemies:
                enemy.update(dt)
                shot = enemy.try_shoot()
                if shot:
                    session.bullets.append(shot)
            for asteroid in session.asteroids:
                asteroid.update(dt)
            for bonus in session.bonuses:
                bonus.update(dt)
            for mine in session.mines:
                mine.update(dt)
            for bullet in session.bullets:
                bullet.update(dt)

            handle_collisions(
                player=session.player,
                bullets=session.bullets,
                enemies=session.enemies,
                asteroids=session.asteroids,
                bonuses=session.bonuses,
                mines=session.mines,
                scoring=session.scoring,
                effects=session.effects,
                player_bonuses=session.player_bonuses,
                sound=sound,
            )
            session.effects.update(dt)
            save_if_needed(session)

            if session.scoring.lives <= 0:
                save_checkpoint(serialize_session(new_session()))
                state = GameState.GAME_OVER
                sound.stop_music()

        if state != GameState.PLAYING:
            session.effects.update(dt)

        # Animate starfield
        speed = 25 + int(difficulty_multiplier(session.scoring.run_time_seconds, session.scoring.score) * 8)
        animated_stars = []
        for sx, sy, size in stars:
            sy += int(speed * dt * size)
            if sy > config.SCREEN_HEIGHT:
                sy = 0
                sx = random.randint(0, config.SCREEN_WIDTH)
            animated_stars.append((sx, sy, size))
        stars = animated_stars

        offset = session.effects.screen_offset()
        draw_scene(screen, session, stars, offset, background)
        if session.effects.flash_time > 0:
            flash = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_alpha = int(120 * (session.effects.flash_time / 0.08))
            flash.fill((255, 255, 255, max(0, min(120, flash_alpha))))
            screen.blit(flash, (0, 0))

        draw_hud(
            surface=screen,
            font=font,
            small_font=small_font,
            score=session.scoring.score,
            lives=session.scoring.lives,
            health=session.scoring.health,
            elapsed_seconds=session.scoring.run_time_seconds,
            score_multiplier=session.scoring.score_multiplier,
        )
        draw_audio_toggles(
            surface=screen,
            font=small_font,
            music_rect=music_rect,
            sound_rect=sound_rect,
            music_on=sound.music_enabled,
            sound_on=sound.sfx_enabled,
        )

        if state == GameState.MENU:
            t1 = menu_font.render("FlyFight", True, config.COLOR_TEXT)
            t2 = small_font.render("Press N - New Game", True, config.COLOR_TEXT)
            t3 = small_font.render("Press C - Continue from checkpoint", True, config.COLOR_TEXT if has_checkpoint() else config.COLOR_WARNING)
            t4 = small_font.render("Move: WASD/Arrows | Shoot: Space", True, config.COLOR_TEXT)
            t5 = small_font.render("F1: Music ON/OFF | F2: Sound ON/OFF", True, config.COLOR_TEXT)
            screen.blit(t1, (config.SCREEN_WIDTH // 2 - t1.get_width() // 2, 210))
            screen.blit(t2, (config.SCREEN_WIDTH // 2 - t2.get_width() // 2, 280))
            screen.blit(t3, (config.SCREEN_WIDTH // 2 - t3.get_width() // 2, 312))
            screen.blit(t4, (config.SCREEN_WIDTH // 2 - t4.get_width() // 2, 350))
            screen.blit(t5, (config.SCREEN_WIDTH // 2 - t5.get_width() // 2, 382))

        if state == GameState.PAUSED:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            label = menu_font.render("Paused", True, config.COLOR_TEXT)
            hint = small_font.render("Press P or Esc to continue", True, config.COLOR_TEXT)
            screen.blit(label, (config.SCREEN_WIDTH // 2 - label.get_width() // 2, 260))
            screen.blit(hint, (config.SCREEN_WIDTH // 2 - hint.get_width() // 2, 305))

        if state == GameState.GAME_OVER:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((8, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            label = menu_font.render("Game Over", True, (255, 155, 155))
            score_text = small_font.render(f"Final score: {session.scoring.score}", True, config.COLOR_TEXT)
            hint = small_font.render("Press R to restart | Esc to quit", True, config.COLOR_TEXT)
            screen.blit(label, (config.SCREEN_WIDTH // 2 - label.get_width() // 2, 245))
            screen.blit(score_text, (config.SCREEN_WIDTH // 2 - score_text.get_width() // 2, 290))
            screen.blit(hint, (config.SCREEN_WIDTH // 2 - hint.get_width() // 2, 325))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    run()

