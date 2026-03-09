"""Visual effect system for explosions and impact feedback."""

from __future__ import annotations

from dataclasses import dataclass
import random
import pygame

from game import assets


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]
    size: int

    def update(self, dt: float) -> None:
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 14 * dt


@dataclass
class ExplosionOverlay:
    """A fading explosion image drawn over the particle burst."""
    x: float
    y: float
    size: int
    sprite_name: str
    life: float
    max_life: float

    def update(self, dt: float) -> None:
        self.life -= dt

    @property
    def alpha_ratio(self) -> float:
        return max(0.0, self.life / self.max_life)


class EffectsSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.overlays: list[ExplosionOverlay] = []
        self.shake_time = 0.0
        self.flash_time = 0.0

    def add_explosion(self, x: int, y: int, big: bool = False, mine_style: bool = False) -> None:
        count = 30 if big else 18
        speed_scale = 240 if big else 160
        palette = [(255, 170, 80), (255, 220, 120), (255, 90, 60)]
        if mine_style:
            palette = [(255, 80, 100), (255, 140, 120), (210, 40, 80)]
        for _ in range(count):
            angle = random.uniform(0, 6.283185307179586)
            speed = random.uniform(55.0, speed_scale)
            vx = speed * pygame.math.Vector2(1, 0).rotate_rad(angle).x
            vy = speed * pygame.math.Vector2(1, 0).rotate_rad(angle).y
            self.particles.append(
                Particle(
                    x=float(x),
                    y=float(y),
                    vx=vx,
                    vy=vy,
                    life=random.uniform(0.2, 0.7),
                    color=random.choice(palette),
                    size=random.randint(2, 5),
                )
            )
        self.shake_time = max(self.shake_time, 0.15 if big else 0.1)
        self.flash_time = max(self.flash_time, 0.08 if big else 0.05)

        # Image overlay — pick randomly between explosion1 / explosion2
        sprite_name = random.choice(["explosion1", "explosion2"])
        overlay_size = 160 if big else 96
        duration = 0.55 if big else 0.38
        self.overlays.append(
            ExplosionOverlay(
                x=float(x),
                y=float(y),
                size=overlay_size,
                sprite_name=sprite_name,
                life=duration,
                max_life=duration,
            )
        )

    def update(self, dt: float) -> None:
        self.shake_time = max(0.0, self.shake_time - dt)
        self.flash_time = max(0.0, self.flash_time - dt)
        self.particles = [p for p in self.particles if (p.update(dt) or True) and p.life > 0.0]
        self.overlays = [o for o in self.overlays if (o.update(dt) or True) and o.life > 0.0]

    def draw(self, surface: pygame.Surface) -> None:
        # Draw image overlays first (behind particles)
        for o in self.overlays:
            sprite = assets.get_explosion(o.sprite_name, o.size, o.size)
            if sprite is not None:
                faded = sprite.copy()
                # Multiply alpha channel for per-pixel-alpha surfaces
                faded.fill(
                    (255, 255, 255, int(255 * o.alpha_ratio)),
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
                rect = faded.get_rect(center=(int(o.x), int(o.y)))
                surface.blit(faded, rect)

        # Draw particles on top
        for particle in self.particles:
            alpha = max(0.0, min(1.0, particle.life / 0.7))
            color = (
                int(particle.color[0] * alpha),
                int(particle.color[1] * alpha),
                int(particle.color[2] * alpha),
            )
            pygame.draw.circle(surface, color, (int(particle.x), int(particle.y)), particle.size)

    def screen_offset(self) -> tuple[int, int]:
        if self.shake_time <= 0.0:
            return (0, 0)
        magnitude = 4 if self.shake_time > 0.08 else 2
        return random.randint(-magnitude, magnitude), random.randint(-magnitude, magnitude)
