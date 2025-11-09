"""Модели данных для конфигурации и описания релизов плагинов."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class AssetPattern:
    """Описание шаблона для бинарника конкретной архитектуры."""

    arch: str
    pattern: str
    rename_to: Optional[str] = None
    archive_member: Optional[str] = None


@dataclass
class PluginSource:
    """Настройки источника релиза."""

    type: str
    owner: str
    repo: str
    release_branch: Optional[str] = None
    tag_prefix: str = ""
    asset_patterns: List[AssetPattern] = field(default_factory=list)


@dataclass
class PluginConfig:
    """Конфигурация плагина."""

    name: str
    branch: str
    source: PluginSource
    release_name_template: str = "{name} {version}"
    release_body_template: str = (
        "Автоматически созданный релиз для {name}.\n"
        "Версия исходного проекта: {version}."
    )
    plugin_description: str = ""
    binary_subdir: str = "bin"

    def expected_architectures(self) -> Iterable[str]:
        """Возвращает список архитектур, заданных в конфигурации."""

        return [pattern.arch for pattern in self.source.asset_patterns]


@dataclass
class ReleaseState:
    """Состояние обработанного релиза."""

    plugin: str
    version: str
    assets: Dict[str, str]

