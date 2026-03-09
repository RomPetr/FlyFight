"""Autosave checkpoint service."""

import json
from pathlib import Path
from typing import Any

from game import config


def save_checkpoint(payload: dict[str, Any]) -> None:
    config.SAVE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = Path(str(config.CHECKPOINT_FILE) + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(config.CHECKPOINT_FILE)


def load_checkpoint() -> dict[str, Any] | None:
    if not config.CHECKPOINT_FILE.exists():
        return None
    try:
        return json.loads(config.CHECKPOINT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def has_checkpoint() -> bool:
    return config.CHECKPOINT_FILE.exists()

