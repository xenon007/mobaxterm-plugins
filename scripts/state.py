"""Загрузка и сохранение состояния обработанных релизов."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import ReleaseState


def load_state(path: Path) -> Optional[ReleaseState]:
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return ReleaseState(plugin=raw["plugin"], version=raw["version"], assets=raw.get("assets", {}))


def save_state(path: Path, state: ReleaseState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "plugin": state.plugin,
        "version": state.version,
        "assets": state.assets,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

