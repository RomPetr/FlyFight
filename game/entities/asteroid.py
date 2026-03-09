"""Asteroid hazard."""

from dataclasses import dataclass, field
import random
import pygame

from game import assets, config


@dataclass
class Asteroid:
    rect: pygame.Rect
    speed: float
    hp: int = 2
    max_hp: int = 2
    size_rank: str = "small"
    _sprite_key: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        size = max(self.rect.width, self.rect.height)
        if size >= 52:
            self.size_rank = "large"
        elif size >= 36:
            self.size_rank = "medium"
        else:
            self.size_rank = "small"
        self.max_hp = {"small": 1, "medium": 2, "large": 3}.get(self.size_rank, 1)
        self._sprite_key = assets.pick_meteor_name(size)

    @classmethod
    def create(cls, x_position: int) -> "Asteroid":
        # Three clear asteroid ranks with size/speed profiles.
        rank = random.choices(["small", "medium", "large"], weights=[0.46, 0.36, 0.18], k=1)[0]
        if rank == "small":
            size = random.randint(22, 30)
            speed = random.uniform(125.0, 180.0)
            hp = 1
        elif rank == "medium":
            size = random.randint(36, 48)
            speed = random.uniform(95.0, 145.0)
            hp = 2
        else:
            size = random.randint(52, 64)
            speed = random.uniform(70.0, 115.0)
            hp = 3

        rect = pygame.Rect(x_position, -size, size, size)
        return cls(rect=rect, speed=speed, hp=hp, size_rank=rank)

    def update(self, dt: float) -> None:
        self.rect.y += int(self.speed * dt)

    def draw(self, surface: pygame.Surface) -> None:
        sprite = assets.get_meteor(self._sprite_key, self.rect.width, self.rect.height)
        if sprite is not None:
            surface.blit(sprite, self.rect.topleft)
        else:
            pygame.draw.ellipse(surface, config.COLOR_ASTEROID, self.rect)

        if self.max_hp > 1:
            ratio = max(0.0, min(1.0, self.hp / self.max_hp))
            bar_bg = pygame.Rect(self.rect.left, self.rect.top - 6, self.rect.width, 4)
            bar_fill = pygame.Rect(self.rect.left, self.rect.top - 6, int(self.rect.width * ratio), 4)
            pygame.draw.rect(surface, (35, 40, 52), bar_bg, border_radius=2)
            pygame.draw.rect(surface, (170, 190, 210), bar_fill, border_radius=2)
