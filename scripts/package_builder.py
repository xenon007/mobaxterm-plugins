"""Сборка архивов плагинов MobaXterm."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

from .models import AssetPattern, PluginConfig

LOGGER = logging.getLogger(__name__)


_ARCHIVE_EXTENSION = {
    "x86": ".mxt3",
    "x64": ".mxt64",
}


def _resolve_archive_name(plugin: PluginConfig, version: str, arch: str) -> str:
    extension = _ARCHIVE_EXTENSION.get(arch, f"-{arch}.zip")
    return f"{plugin.name}-{version}-{arch}{extension}"


def _resolve_internal_name(pattern: AssetPattern, source_path: Path) -> str:
    if pattern.rename_to:
        return pattern.rename_to
    return source_path.name


class PackageBuilder:
    """Утилита для упаковки бинарников в формат mxt."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def build(
        self,
        plugin: PluginConfig,
        pattern: AssetPattern,
        *,
        version: str,
        binary_path: Path,
        release_url: Optional[str] = None,
    ) -> Path:
        archive_name = _resolve_archive_name(plugin, version, pattern.arch)
        archive_path = self._output_dir / archive_name
        metadata = {
            "name": plugin.name,
            "version": version,
            "arch": pattern.arch,
            "description": plugin.plugin_description,
            "source_release": release_url,
        }
        binary_inside = Path(plugin.binary_subdir) / _resolve_internal_name(pattern, binary_path)

        LOGGER.info("Формирование архива %s", archive_path)
        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(binary_path, arcname=str(binary_inside))
            archive.writestr("plugin.json", json.dumps(metadata, ensure_ascii=False, indent=2))
        return archive_path

