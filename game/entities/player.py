"""Player ship entity."""

from dataclasses import dataclass
import pygame

from game import assets, config
from game.entities.bullet import Bullet


@dataclass
class PlayerShip:
    rect: pygame.Rect
    speed: float = config.PLAYER_SPEED
    bullet_cooldown: float = config.BULLET_COOLDOWN
    invulnerable_time: float = 0.0

    _shot_timer: float = 0.0

    @classmethod
    def create(cls) -> "PlayerShip":
        ship_rect = pygame.Rect(0, 0, 36, 42)
        ship_rect.centerx = config.SCREEN_WIDTH // 2
        ship_rect.bottom = config.SCREEN_HEIGHT - 30
        return cls(rect=ship_rect)

    def update(self, dt: float, pressed: pygame.key.ScancodeWrapper) -> None:
        self._shot_timer = max(0.0, self._shot_timer - dt)
        self.invulnerable_time = max(0.0, self.invulnerable_time - dt)

        move_x = 0.0
        move_y = 0.0
        if pressed[pygame.K_LEFT] or pressed[pygame.K_a]:
            move_x -= self.speed * dt
        if pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
            move_x += self.speed * dt
        if pressed[pygame.K_UP] or pressed[pygame.K_w]:
            move_y -= self.speed * dt
        if pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
            move_y += self.speed * dt

        self.rect.x += int(move_x)
        self.rect.y += int(move_y)
        self.rect.clamp_ip(pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def try_shoot(self, pressed: pygame.key.ScancodeWrapper) -> Bullet | None:
        if not (pressed[pygame.K_SPACE] or pressed[pygame.K_RETURN]):
            return None
        if self._shot_timer > 0:
            return None

        self._shot_timer = self.bullet_cooldown
        bullet_rect = pygame.Rect(0, 0, 8, 20)
        bullet_rect.centerx = self.rect.centerx
        bullet_rect.bottom = self.rect.top
        return Bullet(rect=bullet_rect, velocity_y=-config.BULLET_SPEED, from_player=True)

    def draw(self, surface: pygame.Surface) -> None:
        sprite = assets.get_player_ship(self.rect.width, self.rect.height)
        if sprite is not None:
            if self.invulnerable_time > 0:
                tinted = sprite.copy()
                tinted.fill((160, 240, 255, 90), special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(tinted, self.rect.topleft)
            else:
                surface.blit(sprite, self.rect.topleft)
        else:
            color = config.COLOR_PLAYER if self.invulnerable_time <= 0 else (160, 240, 255)
            pygame.draw.polygon(
                surface,
                color,
                [
                    (self.rect.centerx, self.rect.top),
                    (self.rect.right, self.rect.bottom),
                    (self.rect.left, self.rect.bottom),
                ],
            )

