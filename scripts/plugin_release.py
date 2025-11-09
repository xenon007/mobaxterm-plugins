"""Утилита обновления релизов плагинов MobaXterm."""
from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import tarfile
from zipfile import ZipFile, is_zipfile

from .config_loader import ConfigurationError, load_plugins_config
from .github_api import GitHubAPI, GitHubAPIError
from .models import AssetPattern, PluginConfig, ReleaseState
from .package_builder import PackageBuilder
from .state import load_state, save_state

LOGGER = logging.getLogger(__name__)


class PluginReleaseError(RuntimeError):
    """Базовая ошибка сборки релиза плагина."""


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        raise PluginReleaseError("Не удалось определить текущую ветку git") from error
    return result.stdout.strip()


def _origin_repo() -> Tuple[str, str]:
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        raise PluginReleaseError("Не удалось получить адрес origin") from error
    url = result.stdout.strip()
    match = re.search(r"github.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?", url)
    if not match:
        raise PluginReleaseError(f"Не удалось разобрать адрес удалённого репозитория: {url}")
    return match.group("owner"), match.group("repo")


def _ensure_branch(expected: str) -> None:
    branch = _current_branch()
    if branch != expected:
        raise PluginReleaseError(f"Скрипт должен запускаться в ветке {expected}, текущая ветка {branch}")


def _latest_release(api: GitHubAPI, plugin: PluginConfig) -> Tuple[dict, str]:
    releases = api.list_releases(plugin.source.owner, plugin.source.repo)
    if not isinstance(releases, list):
        raise PluginReleaseError("GitHub API вернул неожиданный ответ при запросе релизов")

    prefix = plugin.source.tag_prefix
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        if plugin.source.release_branch and release.get("target_commitish") != plugin.source.release_branch:
            continue
        tag = release.get("tag_name", "")
        if prefix and not tag.startswith(prefix):
            continue
        version = tag[len(prefix) :] if prefix else tag
        return release, version
    raise PluginReleaseError("Подходящих релизов не найдено")


def _match_assets(patterns: Iterable[AssetPattern], release: dict) -> Dict[str, dict]:
    assets = release.get("assets", [])
    result: Dict[str, dict] = {}
    for pattern in patterns:
        regex = re.compile(pattern.pattern)
        for asset in assets:
            if regex.search(asset.get("name", "")):
                result[pattern.arch] = asset
                break
        else:
            raise PluginReleaseError(
                f"Для архитектуры {pattern.arch} не найден подходящий бинарник по шаблону {pattern.pattern}"
            )
    return result


def _download_asset(asset: dict, destination: Path, token: str | None) -> Path:
    url = asset.get("browser_download_url")
    if not url:
        raise PluginReleaseError("У релиза отсутствует ссылка на скачивание бинарника")

    request = Request(url)
    request.add_header("User-Agent", "mobaxterm-plugin-updater")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Загрузка %s", url)
    try:
        with urlopen(request) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    except HTTPError as error:
        raise PluginReleaseError(f"Не удалось скачать файл {url}: {error}") from error
    return destination


def _extract_from_archive(archive_path: Path, pattern: AssetPattern, workdir: Path) -> Path:
    member_regex = re.compile(pattern.archive_member) if pattern.archive_member else None
    extracted_dir = workdir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    if is_zipfile(archive_path):
        with ZipFile(archive_path) as archive:
            members = [m for m in archive.namelist() if not m.endswith("/")]
            target = _select_member(members, member_regex, archive_path)
            destination = extracted_dir / Path(target).name
            with archive.open(target) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)
            return destination

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:*") as archive:
            members = [m for m in archive.getmembers() if m.isfile()]
            target_name = _select_member([m.name for m in members], member_regex, archive_path)
            member = archive.getmember(target_name)
            destination = extracted_dir / Path(member.name).name
            with archive.extractfile(member) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)
            return destination

    if member_regex:
        raise PluginReleaseError(
            f"Архив {archive_path} не поддерживается для извлечения, необходимо распаковать вручную"
        )
    return archive_path


def _select_member(members: Iterable[str], regex: re.Pattern[str] | None, archive_path: Path) -> str:
    candidates = [m for m in members if not Path(m).name.startswith(".")]
    if regex:
        for member in candidates:
            if regex.search(member):
                return member
        raise PluginReleaseError(f"В архиве {archive_path} не найден файл по шаблону {regex.pattern}")
    if len(candidates) == 1:
        return candidates[0]
    raise PluginReleaseError(
        f"В архиве {archive_path} найдено несколько файлов, укажите 'archive_member' в конфигурации"
    )


def _prepare_binary(binary_path: Path, pattern: AssetPattern, workdir: Path) -> Path:
    if binary_path.suffix.lower() in {".zip", ".gz", ".tgz", ".tar"} or is_zipfile(binary_path):
        return _extract_from_archive(binary_path, pattern, workdir)
    return binary_path


def _archive_assets(
    plugin: PluginConfig,
    version: str,
    patterns: List[AssetPattern],
    matched_assets: Dict[str, dict],
    temp_dir: Path,
    output_dir: Path,
    release_url: str | None,
    token: str | None,
) -> ReleaseState:
    builder = PackageBuilder(output_dir)
    built_assets: Dict[str, str] = {}
    for pattern in patterns:
        asset = matched_assets[pattern.arch]
        binary_path = temp_dir / asset["name"]
        _download_asset(asset, binary_path, token)
        prepared_binary = _prepare_binary(binary_path, pattern, temp_dir)
        archive_path = builder.build(
            plugin,
            pattern,
            version=version,
            binary_path=prepared_binary,
            release_url=release_url,
        )
        built_assets[pattern.arch] = str(archive_path)
    return ReleaseState(plugin=plugin.name, version=version, assets=built_assets)


def _upload_release(
    api: GitHubAPI,
    repo_owner: str,
    repo_name: str,
    plugin: PluginConfig,
    state: ReleaseState,
    release_name: str,
    release_body: str,
    target_branch: str,
) -> None:
    tag = f"{plugin.name}-v{state.version}"
    existing = api.get_release_by_tag(repo_owner, repo_name, tag)
    if existing:
        LOGGER.info("Релиз %s уже существует, загрузка ассетов", tag)
        release = existing
    else:
        LOGGER.info("Создание релиза %s", tag)
        release = api.create_release(
            repo_owner,
            repo_name,
            tag_name=tag,
            target_commitish=target_branch,
            name=release_name,
            body=release_body,
            draft=False,
            prerelease=False,
        )
    upload_url = release.get("upload_url")
    if not upload_url:
        raise PluginReleaseError("GitHub не вернул ссылку для загрузки ассетов")

    for arch, path in state.assets.items():
        LOGGER.info("Загрузка архива для %s: %s", arch, path)
        api.upload_asset(upload_url, path, content_type="application/zip")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Проверка обновлений плагина и формирование релиза")
    parser.add_argument("--plugin", required=True, help="Название плагина из конфигурации")
    parser.add_argument("--config", default="data/plugins.json", help="Путь до файла конфигурации")
    parser.add_argument("--output-dir", default="dist", help="Каталог для собранных архивов")
    parser.add_argument("--state-dir", default="state", help="Каталог для хранения обработанных версий")
    parser.add_argument("--publish", action="store_true", help="Создать релиз в текущем репозитории")
    parser.add_argument("--force", action="store_true", help="Игнорировать уже обработанную версию")
    parser.add_argument(
        "--ignore-branch",
        action="store_true",
        help="Не проверять соответствие текущей ветки требуемой ветке плагина",
    )
    parser.add_argument("--verbose", action="store_true", help="Подробный вывод логов")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    _configure_logging(args.verbose)

    try:
        config = load_plugins_config(Path(args.config))
    except ConfigurationError as error:
        LOGGER.error("%s", error)
        return 1

    plugin = config.get(args.plugin)
    if not plugin:
        LOGGER.error("Плагин %s не найден в конфигурации", args.plugin)
        return 1

    if not args.ignore_branch:
        try:
            _ensure_branch(plugin.branch)
        except PluginReleaseError as error:
            LOGGER.error("%s", error)
            return 1

    token = os.getenv("GITHUB_TOKEN")
    api = GitHubAPI(token=token)

    try:
        release, version = _latest_release(api, plugin)
    except (PluginReleaseError, GitHubAPIError) as error:
        LOGGER.error("%s", error)
        return 1

    state_path = Path(args.state_dir) / f"{plugin.name}.json"
    previous_state = load_state(state_path)
    if previous_state and previous_state.version == version and not args.force:
        LOGGER.info("Актуальная версия %s уже обработана", version)
        return 0

    patterns = list(plugin.source.asset_patterns)
    try:
        matched_assets = _match_assets(patterns, release)
    except PluginReleaseError as error:
        LOGGER.error("%s", error)
        return 1

    temp_dir = Path(".tmp") / f"{plugin.name}-{version}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        state = _archive_assets(
            plugin,
            version,
            patterns,
            matched_assets,
            temp_dir,
            Path(args.output_dir),
            release_url=release.get("html_url"),
            token=token,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    save_state(state_path, state)
    LOGGER.info("Сохранено состояние для %s версии %s", plugin.name, version)

    if args.publish:
        try:
            owner, repo = _origin_repo()
        except PluginReleaseError as error:
            LOGGER.error("%s", error)
            return 1
        release_name = plugin.release_name_template.format(name=plugin.name, version=version)
        release_body = plugin.release_body_template.format(name=plugin.name, version=version)
        try:
            _upload_release(
                api,
                owner,
                repo,
                plugin,
                state,
                release_name,
                release_body,
                plugin.branch,
            )
        except (PluginReleaseError, GitHubAPIError) as error:
            LOGGER.error("%s", error)
            return 1

    LOGGER.info("Плагин %s обновлён до версии %s", plugin.name, version)
    return 0


if __name__ == "__main__":
    sys.exit(main())

