"""Mine hazard entity."""

from dataclasses import dataclass
import pygame

from game import assets, config


@dataclass
class Mine:
    rect: pygame.Rect
    speed: float = 140.0

    @classmethod
    def create(cls, x_position: int) -> "Mine":
        rect = pygame.Rect(x_position, -26, 26, 26)
        return cls(rect=rect)

    def update(self, dt: float) -> None:
        self.rect.y += int(self.speed * dt)

    def draw(self, surface: pygame.Surface) -> None:
        sprite = assets.get_mine(self.rect.width, self.rect.height)
        if sprite is not None:
            surface.blit(sprite, self.rect.topleft)
        else:
            pygame.draw.circle(surface, config.COLOR_MINE, self.rect.center, self.rect.width // 2)
            pygame.draw.circle(surface, (35, 10, 20), self.rect.center, self.rect.width // 4)

