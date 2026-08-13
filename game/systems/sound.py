"""Sound management for FlyFight."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pygame

from game import config

logger = logging.getLogger(__name__)

MUSIC_FILE_PATTERN = re.compile(r"^music(\d+)\.(wav|ogg|mp3)$", re.IGNORECASE)
MUSIC_EXTENSIONS = (".wav", ".ogg", ".mp3")
EXT_PRIORITY = {".wav": 0, ".ogg": 1, ".mp3": 2}


def discover_music_tracks(sounds_dir: Path) -> list[tuple[int, Path]]:
    """Find music<number>.{wav,ogg,mp3} files sorted by numeric track id."""
    if not sounds_dir.is_dir():
        logger.warning("Music directory not found: %s", sounds_dir)
        return []

    by_number: dict[int, list[Path]] = {}
    for path in sounds_dir.iterdir():
        if not path.is_file():
            continue
        match = MUSIC_FILE_PATTERN.match(path.name)
        if not match:
            continue
        number = int(match.group(1))
        by_number.setdefault(number, []).append(path)

    tracks: list[tuple[int, Path]] = []
    for number in sorted(by_number.keys()):
        paths = by_number[number]
        if len(paths) > 1:
            paths.sort(key=lambda p: EXT_PRIORITY.get(p.suffix.lower(), 99))
            skipped = ", ".join(p.name for p in paths[1:])
            logger.warning(
                "Multiple files for music track %d; using %s (skipped: %s)",
                number,
                paths[0].name,
                skipped,
            )
        tracks.append((number, paths[0]))

    if not tracks:
        logger.warning(
            "No music tracks found in %s (expected music<number>.wav|.ogg|.mp3)",
            sounds_dir,
        )
    else:
        names = ", ".join(path.name for _, path in tracks)
        logger.info("Discovered music tracks: %s", names)

    return tracks


class SoundManager:
    """Loads and plays game sounds and background music tracks."""

    def __init__(self) -> None:
        self._ok: bool = pygame.mixer.get_init() is not None
        self._shoot: pygame.mixer.Sound | None = None
        self._shoot_blaster: pygame.mixer.Sound | None = None
        self._death: pygame.mixer.Sound | None = None
        self._pickup: pygame.mixer.Sound | None = None
        self._pickup_weapon: pygame.mixer.Sound | None = None
        self._level_up: pygame.mixer.Sound | None = None
        self.sfx_enabled: bool = True
        self.music_volume: float = config.MUSIC_VOLUME

        self._tracks: list[tuple[int, Path]] = discover_music_tracks(config.SOUNDS_DIR)
        self._track_index: int = -1  # index into _tracks, -1 = Music Off

        self._load_settings()
        self._apply_saved_music_selection()

        if not self._ok:
            return

        self._shoot = self._load(config.SOUNDS_DIR / "shoot.wav")
        self._shoot_blaster = self._load(config.SOUNDS_DIR / "mixkit-arcade-mechanical-bling-210.wav")
        self._death = self._load(config.SOUNDS_DIR / "death.wav")
        self._pickup = self._load(config.SOUNDS_DIR / "unlock_gift.wav")
        self._pickup_weapon = self._load(config.SOUNDS_DIR / "attaching-a-blaster-to-create-more-powerful-weapons.wav")
        self._level_up = self._load(config.SOUNDS_DIR / "level_increased.wav")

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

        if self._track_index >= 0:
            self._play_current_track()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, path: Path) -> pygame.mixer.Sound | None:
        try:
            return pygame.mixer.Sound(str(path))
        except (pygame.error, FileNotFoundError, OSError) as exc:
            logger.warning("Failed to load sound %s: %s", path.name, exc)
            return None

    def _index_for_number(self, track_number: int) -> int | None:
        for index, (number, _path) in enumerate(self._tracks):
            if number == track_number:
                return index
        return None

    def _apply_saved_music_selection(self) -> None:
        if not self._tracks:
            self._track_index = -1
            return
        if self._saved_track_number < 0:
            self._track_index = -1
            return
        index = self._index_for_number(self._saved_track_number)
        if index is None:
            logger.warning(
                "Saved music track Music %d not found; falling back to Music Off",
                self._saved_track_number,
            )
            self._track_index = -1
            return
        self._track_index = index

    def _load_settings(self) -> None:
        self._saved_track_number = 1
        self.sfx_enabled = True
        settings_path = config.AUDIO_SETTINGS_FILE
        if not settings_path.exists():
            return
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read audio settings: %s", exc)
            return

        if "music_track_number" in data:
            self._saved_track_number = int(data["music_track_number"])
        elif data.get("music_enabled") is False:
            self._saved_track_number = -1
        else:
            self._saved_track_number = 1

        self.sfx_enabled = bool(data.get("sfx_enabled", True))

    def _save_settings(self) -> None:
        config.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        track_number = -1
        if self._track_index >= 0:
            track_number = self._tracks[self._track_index][0]
        payload = {
            "music_track_number": track_number,
            "sfx_enabled": self.sfx_enabled,
        }
        tmp_path = Path(str(config.AUDIO_SETTINGS_FILE) + ".tmp")
        try:
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp_path.replace(config.AUDIO_SETTINGS_FILE)
        except OSError as exc:
            logger.warning("Could not save audio settings: %s", exc)

    def _play_current_track(self) -> bool:
        if not self._ok or self._track_index < 0 or not self._tracks:
            return False
        _number, path = self._tracks[self._track_index]
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            return True
        except pygame.error as exc:
            logger.error("Failed to play music file %s: %s", path.name, exc)
            return False

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

    @property
    def music_button_label(self) -> str:
        if self._track_index < 0 or not self._tracks:
            return "Music Off"
        track_number, _path = self._tracks[self._track_index]
        return f"Music {track_number}"

    @property
    def music_enabled(self) -> bool:
        return self._track_index >= 0

    def start_music(self) -> None:
        if self._track_index < 0:
            return
        self._play_current_track()

    def stop_music(self) -> None:
        if not self._ok:
            return
        try:
            pygame.mixer.music.stop()
        except pygame.error as exc:
            logger.warning("Failed to stop music: %s", exc)

    def pause_music(self) -> None:
        if not self._ok or self._track_index < 0:
            return
        try:
            pygame.mixer.music.pause()
        except pygame.error as exc:
            logger.warning("Failed to pause music: %s", exc)

    def resume_music(self) -> None:
        if not self._ok or self._track_index < 0:
            return
        try:
            pygame.mixer.music.unpause()
        except pygame.error as exc:
            logger.warning("Failed to resume music: %s", exc)

    def cycle_music(self, should_play_now: bool = True) -> None:
        """Cycle Music 1 -> ... -> Music N -> Music Off -> Music 1."""
        if not self._tracks:
            self._track_index = -1
            self.stop_music()
            self._save_settings()
            return

        if self._track_index == -1:
            first_index = self._index_for_number(1)
            if first_index is None:
                logger.warning("Music 1 requested but music1.* was not found")
                self._save_settings()
                return
            self._track_index = first_index
        elif self._track_index < len(self._tracks) - 1:
            self._track_index += 1
        else:
            self._track_index = -1
            self.stop_music()
            self._save_settings()
            return

        if should_play_now:
            if not self._play_current_track():
                self._skip_failed_track_forward(should_play_now=True)
        self._save_settings()

    def _skip_failed_track_forward(self, should_play_now: bool) -> None:
        """Advance to next playable track after a load failure."""
        start = self._track_index
        while self._track_index >= 0:
            if should_play_now and self._play_current_track():
                return
            if self._track_index < len(self._tracks) - 1:
                self._track_index += 1
            else:
                self._track_index = -1
                self.stop_music()
                return
        if start != self._track_index:
            logger.warning("All music tracks failed to load; switched to Music Off")

    def toggle_sfx(self) -> bool:
        self.sfx_enabled = not self.sfx_enabled
        self._save_settings()
        return self.sfx_enabled
