"""Bullet projectiles used by player and enemies."""

from dataclasses import dataclass
import random
import pygame

from game import assets


@dataclass
class Bullet:
    rect: pygame.Rect
    velocity_y: float
    from_player: bool
    damage: int = 1

    def update(self, dt: float) -> None:
        self.rect.y += int(self.velocity_y * dt)

    def draw(self, surface: pygame.Surface) -> None:
        if self.from_player:
            sprite = assets.get_player_laser(self.rect.width, self.rect.height)
        else:
            sprite = assets.get_enemy_laser(self.rect.width, self.rect.height)

        if sprite is not None:
            if self.from_player:
                # Bright laser trail and glow for clearer player shots.
                heavy = self.damage >= 3
                glow_outer = (180, 90, 255) if heavy else (90, 190, 255)
                glow_inner = (255, 190, 255) if heavy else (170, 235, 255)
                arrow_color = (255, 220, 255) if heavy else (200, 245, 255)
                trail_len = 14 if heavy else 10
                glow_radius = max(2, self.rect.width // 2 + 2)
                pygame.draw.circle(surface, glow_outer, self.rect.center, glow_radius)
                pygame.draw.circle(surface, glow_inner, self.rect.center, max(1, glow_radius - 1))
                pygame.draw.line(
                    surface,
                    glow_outer,
                    (self.rect.centerx, self.rect.bottom),
                    (self.rect.centerx, self.rect.bottom + trail_len),
                    max(1, self.rect.width // 3),
                )
                pygame.draw.polygon(
                    surface,
                    arrow_color,
                    [
                        (self.rect.centerx, self.rect.top - 4),
                        (self.rect.centerx - max(1, self.rect.width // 3), self.rect.top + 2),
                        (self.rect.centerx + max(1, self.rect.width // 3), self.rect.top + 2),
                    ],
                )

            else:
                # Enemy laser glow/trail for better readability in flight.
                elite_beam = self.damage >= 100
                glow_outer = (255, 90, 120) if not elite_beam else (255, 80, 210)
                glow_inner = (255, 170, 190) if not elite_beam else (255, 180, 245)
                trail_len = 10 if not elite_beam else 14
                glow_radius = max(2, self.rect.width // 2 + (2 if elite_beam else 1))
                pygame.draw.circle(surface, glow_outer, self.rect.center, glow_radius)
                pygame.draw.circle(surface, glow_inner, self.rect.center, max(1, glow_radius - 1))
                pygame.draw.line(
                    surface,
                    glow_outer,
                    (self.rect.centerx, self.rect.top - trail_len),
                    (self.rect.centerx, self.rect.top),
                    max(1, self.rect.width // 3),
                )

            surface.blit(sprite, self.rect.topleft)
            if self.from_player:
                for _ in range(2):
                    sx = self.rect.centerx + random.randint(-3, 3)
                    sy = self.rect.bottom + random.randint(-2, 5)
                    if self.damage >= 3:
                        spark_color = random.choice([(255, 190, 255), (255, 130, 230), (210, 160, 255)])
                    else:
                        spark_color = random.choice([(255, 220, 120), (255, 245, 180), (140, 220, 255)])
                    pygame.draw.circle(surface, spark_color, (sx, sy), random.randint(1, 2))
            else:
                spark_count = 3 if self.damage >= 100 else 1
                for _ in range(spark_count):
                    sx = self.rect.centerx + random.randint(-2, 2)
                    sy = self.rect.top - random.randint(0, 5)
                    if self.damage >= 100:
                        spark_color = random.choice([(255, 120, 220), (255, 180, 245), (255, 120, 160)])
                    else:
                        spark_color = random.choice([(255, 130, 130), (255, 190, 160)])
                    pygame.draw.circle(surface, spark_color, (sx, sy), random.randint(1, 2))
        else:
            color = (255, 230, 120) if self.from_player else (255, 80, 80)
            pygame.draw.rect(surface, color, self.rect)

