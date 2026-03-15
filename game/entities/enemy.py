"""Enemy ship entities with tiers."""

from dataclasses import dataclass
import random
import pygame

from game import assets, config
from game.entities.bullet import Bullet


TIER_ORDER = ["light", "medium", "heavy", "elite"]


@dataclass
class EnemyShip:
    tier: str
    rect: pygame.Rect
    hp: int
    max_hp: int
    speed: float
    point_value: int
    shot_cd: float
    shot_timer: float

    @classmethod
    def create(cls, tier: str, x_position: int) -> "EnemyShip":
        data = config.ENEMY_TIER_CONFIG[tier]
        size = data["size"]
        rect = pygame.Rect(x_position, -size, size, size)
        return cls(
            tier=tier,
            rect=rect,
            hp=data["hp"],
            max_hp=data["hp"],
            speed=data["speed"],
            point_value=data["points"],
            shot_cd=data["shot_cd"],
            shot_timer=random.uniform(0.0, data["shot_cd"]),
        )

    def update(self, dt: float) -> None:
        self.rect.y += int(self.speed * dt)
        self.shot_timer = max(0.0, self.shot_timer - dt)

    def try_shoot(self) -> list[Bullet]:
        if self.shot_timer > 0.0:
            return []
        self.shot_timer = self.shot_cd
        fire_chance_by_tier = {
            "light": 0.30,
            "medium": 0.38,
            "heavy": 0.46,
            "elite": 0.54,
        }
        if random.random() > fire_chance_by_tier.get(self.tier, 0.35):
            return []

        if self.tier == "elite":
            # 5-laser volley: two from each wing + one from the nose.
            shots: list[Bullet] = []
            offsets = (-18, -9, 0, 9, 18)
            for dx in offsets:
                bullet_rect = pygame.Rect(0, 0, 7, 18)
                bullet_rect.centerx = self.rect.centerx + dx
                bullet_rect.top = self.rect.bottom - 2
                # damage=100 is treated as instant life loss on hit.
                shots.append(Bullet(rect=bullet_rect, velocity_y=250.0, from_player=False, damage=100))
            return shots

        bullet_rect = pygame.Rect(0, 0, 5, 13)
        bullet_rect.centerx = self.rect.centerx
        bullet_rect.top = self.rect.bottom
        return [Bullet(rect=bullet_rect, velocity_y=220.0, from_player=False, damage=1)]

    def draw(self, surface: pygame.Surface) -> None:
        sprite = assets.get_enemy_ship(self.tier, self.rect.width)
        if sprite is not None:
            surface.blit(sprite, self.rect.topleft)
        else:
            color_map = {
                "light": (180, 220, 255),
                "medium": (255, 190, 120),
                "heavy": (255, 120, 120),
                "elite": (210, 120, 255),
            }
            pygame.draw.rect(surface, color_map.get(self.tier, (220, 220, 220)), self.rect, border_radius=6)

        # Small health bar above enemy (1/2/3-hit readability).
        if self.max_hp > 1:
            ratio = max(0.0, min(1.0, self.hp / self.max_hp))
            bar_bg = pygame.Rect(self.rect.left, self.rect.top - 6, self.rect.width, 4)
            bar_fill = pygame.Rect(self.rect.left, self.rect.top - 6, int(self.rect.width * ratio), 4)
            pygame.draw.rect(surface, (35, 40, 52), bar_bg, border_radius=2)
            pygame.draw.rect(surface, (255, 120, 120), bar_fill, border_radius=2)

