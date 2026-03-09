"""HUD rendering."""

import pygame

from game import config


def format_time(seconds: float) -> str:
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def draw_hud(
    surface: pygame.Surface,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    score: int,
    lives: int,
    health: float,
    elapsed_seconds: float,
    score_multiplier: float,
) -> None:
    score_text = font.render(f"Score: {score}", True, config.COLOR_TEXT)
    lives_text = font.render(f"Lives: {lives}", True, config.COLOR_TEXT)
    health_text = font.render(f"HP: {int(max(0, min(100, health)))}%", True, config.COLOR_TEXT)
    timer_text = font.render(f"ET: {format_time(elapsed_seconds)}", True, config.COLOR_TEXT)
    multi_text = small_font.render(f"x{score_multiplier:.2f}", True, (180, 255, 200))

    surface.blit(score_text, (16, 12))
    surface.blit(lives_text, (16, 44))
    surface.blit(health_text, (16, 76))
    surface.blit(timer_text, (config.SCREEN_WIDTH - timer_text.get_width() - 16, 12))
    surface.blit(multi_text, (config.SCREEN_WIDTH - multi_text.get_width() - 16, 50))

    bar_bg = pygame.Rect(16, 108, 210, 16)
    health_ratio = max(0.0, min(1.0, health / 100.0))
    bar_fill = pygame.Rect(16, 108, int(210 * health_ratio), 16)
    bar_color = (60, 210, 110) if health_ratio > 0.5 else (230, 190, 60) if health_ratio > 0.2 else (230, 80, 80)
    pygame.draw.rect(surface, (40, 50, 70), bar_bg, border_radius=6)
    pygame.draw.rect(surface, bar_color, bar_fill, border_radius=6)
    pygame.draw.rect(surface, (220, 230, 245), bar_bg, width=2, border_radius=6)


def _draw_toggle(
    surface: pygame.Surface,
    font: pygame.font.Font,
    rect: pygame.Rect,
    label: str,
    is_on: bool,
) -> None:
    bg_on = (40, 145, 80)
    bg_off = (145, 45, 55)
    border = (225, 235, 250)
    text_color = (245, 250, 255)

    pygame.draw.rect(surface, bg_on if is_on else bg_off, rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=10)
    text = f"{label} {'ON' if is_on else 'OFF'}"
    text_surface = font.render(text, True, text_color)
    tx = rect.centerx - text_surface.get_width() // 2
    ty = rect.centery - text_surface.get_height() // 2
    surface.blit(text_surface, (tx, ty))


def draw_audio_toggles(
    surface: pygame.Surface,
    font: pygame.font.Font,
    music_rect: pygame.Rect,
    sound_rect: pygame.Rect,
    music_on: bool,
    sound_on: bool,
) -> None:
    _draw_toggle(surface, font, music_rect, "Music", music_on)
    _draw_toggle(surface, font, sound_rect, "Sound", sound_on)


def draw_ship_health_bar(surface: pygame.Surface, ship_rect: pygame.Rect, health: float) -> None:
    width = max(28, ship_rect.width + 10)
    bar_x = ship_rect.centerx - width // 2
    bar_y = ship_rect.bottom + 6
    bg = pygame.Rect(bar_x, bar_y, width, 6)
    ratio = max(0.0, min(1.0, health / 100.0))
    fill = pygame.Rect(bar_x, bar_y, int(width * ratio), 6)
    color = (80, 235, 130) if ratio > 0.5 else (245, 195, 70) if ratio > 0.2 else (245, 85, 85)
    pygame.draw.rect(surface, (20, 24, 32), bg, border_radius=4)
    pygame.draw.rect(surface, color, fill, border_radius=4)
    pygame.draw.rect(surface, (225, 235, 250), bg, width=1, border_radius=4)

