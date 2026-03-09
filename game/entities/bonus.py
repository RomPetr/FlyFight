"""Bonus and gift pickups."""

from dataclasses import dataclass
import pygame

from game import assets, config

BONUS_TYPES = ("shield", "weapon", "strong_laser", "score", "speed", "life")


@dataclass
class BonusPickup:
    bonus_type: str
    rect: pygame.Rect
    speed: float = 115.0

    @classmethod
    def create(cls, bonus_type: str, x_position: int) -> "BonusPickup":
        rect = pygame.Rect(x_position, -20, 20, 20)
        return cls(bonus_type=bonus_type, rect=rect)

    def update(self, dt: float) -> None:
        self.rect.y += int(self.speed * dt)

    def draw(self, surface: pygame.Surface) -> None:
        sprite = assets.get_bonus(self.bonus_type, self.rect.width, self.rect.height)
        if sprite is not None:
            surface.blit(sprite, self.rect.topleft)
        else:
            colors = {
                "shield": (80, 220, 255),
                "weapon": (255, 210, 80),
                "strong_laser": (255, 120, 220),
                "score": (160, 255, 120),
                "speed": (255, 150, 80),
                "life": (255, 90, 180),
            }
            color = colors.get(self.bonus_type, config.COLOR_BONUS)
            pygame.draw.rect(surface, color, self.rect, border_radius=4)
            pygame.draw.rect(surface, (25, 25, 35), self.rect, width=2, border_radius=4)

