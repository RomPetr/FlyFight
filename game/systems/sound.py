"""Sound management for FlyFight."""

from __future__ import annotations

import json
from pathlib import Path

import pygame

from game import config


class SoundManager:
    """Loads and plays all game sounds.  Fails silently if audio is unavailable."""

    def __init__(self) -> None:
        self._ok: bool = pygame.mixer.get_init() is not None
        self._shoot: pygame.mixer.Sound | None = None
        self._shoot_blaster: pygame.mixer.Sound | None = None
        self._death: pygame.mixer.Sound | None = None
        self._pickup: pygame.mixer.Sound | None = None
        self._pickup_weapon: pygame.mixer.Sound | None = None
        self._level_up: pygame.mixer.Sound | None = None
        self._music_loaded: bool = False
        self.music_enabled: bool = True
        self.sfx_enabled: bool = True

        self._load_settings()

        if not self._ok:
            return

        self._shoot = self._load(config.SOUNDS_DIR / "shoot.wav")
        self._shoot_blaster = self._load(config.SOUNDS_DIR / "mixkit-arcade-mechanical-bling-210.wav")
        self._death = self._load(config.SOUNDS_DIR / "death.wav")
        self._pickup = self._load(config.SOUNDS_DIR / "unlock_gift.wav")
        self._pickup_weapon = self._load(config.SOUNDS_DIR / "attaching-a-blaster-to-create-more-powerful-weapons.wav")
        self._level_up = self._load(config.SOUNDS_DIR / "level_increased.wav")
        self._music_loaded = self._load_music(config.SOUNDS_DIR / "music.wav")

        if self._shoot:
            self._shoot.set_volume(0.55)
        if self._shoot_blaster:
            self._shoot_blaster.set_volume(0.65)
        if self._death:
            self._death.set_volume(0.9)
        if self._pickup:
            self._pickup.set_volume(0.8)
        if self._pickup_weapon:
            self._pickup_weapon.set_volume(0.85)
        if self._level_up:
            self._level_up.set_volume(0.9)
        if self._music_loaded:
            pygame.mixer.music.set_volume(0.45)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, path: Path) -> pygame.mixer.Sound | None:
        try:
            return pygame.mixer.Sound(str(path))
        except (pygame.error, FileNotFoundError, OSError):
            return None

    def _load_music(self, path: Path) -> bool:
        try:
            pygame.mixer.music.load(str(path))
            return True
        except (pygame.error, FileNotFoundError, OSError):
            return False

    def _load_settings(self) -> None:
        settings_path = config.AUDIO_SETTINGS_FILE
        if not settings_path.exists():
            return
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.music_enabled = bool(data.get("music_enabled", True))
        self.sfx_enabled = bool(data.get("sfx_enabled", True))

    def _save_settings(self) -> None:
        config.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "music_enabled": self.music_enabled,
            "sfx_enabled": self.sfx_enabled,
        }
        tmp_path = Path(str(config.AUDIO_SETTINGS_FILE) + ".tmp")
        try:
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp_path.replace(config.AUDIO_SETTINGS_FILE)
        except OSError:
            pass

    # ------------------------------------------------------------------
    # Sound-effect playback
    # ------------------------------------------------------------------

    def play_shoot(self, weapon_level: int = 1) -> None:
        if not self.sfx_enabled:
            return
        if weapon_level > 1 and self._shoot_blaster:
            self._shoot_blaster.play()
            return
        if self._shoot:
            self._shoot.play()

    def play_death(self) -> None:
        if self.sfx_enabled and self._death:
            self._death.play()

    def play_pickup(self) -> None:
        if self.sfx_enabled and self._pickup:
            self._pickup.play()

    def play_weapon_upgrade_pickup(self) -> None:
        if self.sfx_enabled and self._pickup_weapon:
            self._pickup_weapon.play()

    def play_level_up(self) -> None:
        if self.sfx_enabled and self._level_up:
            self._level_up.play()

    # ------------------------------------------------------------------
    # Music control
    # ------------------------------------------------------------------

    def start_music(self) -> None:
        if not (self.music_enabled and self._ok and self._music_loaded):
            return
        try:
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def stop_music(self) -> None:
        if not self._ok:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass

    def pause_music(self) -> None:
        if not self._ok:
            return
        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass

    def resume_music(self) -> None:
        if not (self.music_enabled and self._ok):
            return
        try:
            pygame.mixer.music.unpause()
        except pygame.error:
            pass

    def toggle_music(self, should_play_now: bool = True) -> bool:
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()
        elif should_play_now:
            self.start_music()
        self._save_settings()
        return self.music_enabled

    def toggle_sfx(self) -> bool:
        self.sfx_enabled = not self.sfx_enabled
        self._save_settings()
        return self.sfx_enabled
