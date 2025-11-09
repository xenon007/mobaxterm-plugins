"""Загрузка конфигурации плагинов из JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable

from .models import AssetPattern, PluginConfig, PluginSource


class ConfigurationError(RuntimeError):
    """Ошибка чтения конфигурации."""


def _load_asset_patterns(items: Iterable[dict]) -> Iterable[AssetPattern]:
    for item in items:
        if "arch" not in item or "pattern" not in item:
            raise ConfigurationError("Каждый шаблон должен содержать поля 'arch' и 'pattern'.")
        yield AssetPattern(
            arch=item["arch"],
            pattern=item["pattern"],
            rename_to=item.get("rename_to"),
            archive_member=item.get("archive_member"),
        )


def _load_source(raw_source: dict) -> PluginSource:
    required = {"type", "owner", "repo"}
    missing = required - raw_source.keys()
    if missing:
        raise ConfigurationError(f"В описании источника отсутствуют поля: {', '.join(sorted(missing))}")

    asset_patterns = list(_load_asset_patterns(raw_source.get("asset_patterns", [])))
    if raw_source["type"] != "github":
        raise ConfigurationError("На данный момент поддерживается только тип источника 'github'.")

    return PluginSource(
        type=raw_source["type"],
        owner=raw_source["owner"],
        repo=raw_source["repo"],
        release_branch=raw_source.get("release_branch"),
        tag_prefix=raw_source.get("tag_prefix", ""),
        asset_patterns=asset_patterns,
    )


def load_plugins_config(config_path: Path) -> Dict[str, PluginConfig]:
    """Загружает конфигурацию плагинов."""

    if not config_path.exists():
        raise ConfigurationError(f"Файл конфигурации {config_path} не найден.")

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    plugins = {}

    for item in raw.get("plugins", []):
        if "name" not in item or "branch" not in item or "source" not in item:
            raise ConfigurationError("Каждый плагин должен содержать поля 'name', 'branch', 'source'.")
        source = _load_source(item["source"])
        config = PluginConfig(
            name=item["name"],
            branch=item["branch"],
            source=source,
            release_name_template=item.get("release_name_template", "{name} {version}"),
            release_body_template=item.get(
                "release_body_template",
                "Автоматически созданный релиз для {name}.\nВерсия исходного проекта: {version}.",
            ),
            plugin_description=item.get("plugin_description", ""),
            binary_subdir=item.get("binary_subdir", "bin"),
        )
        plugins[config.name] = config
    return plugins
