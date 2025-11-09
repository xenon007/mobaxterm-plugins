"""Минимальный клиент GitHub API на базе стандартной библиотеки."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


LOGGER = logging.getLogger(__name__)


@dataclass
class GitHubAPIError(RuntimeError):
    """Ошибка при работе с GitHub API."""

    status: int
    message: str
    response: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"GitHub API error {self.status}: {self.message}"


class GitHubAPI:
    """Простой клиент GitHub API."""

    def __init__(self, token: Optional[str] = None, api_url: str = "https://api.github.com") -> None:
        self._token = token
        self._api_url = api_url.rstrip("/") + "/"

    def _build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "mobaxterm-plugin-updater",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
        raw_url: bool = False,
    ) -> Dict[str, Any]:
        url = path if raw_url else urljoin(self._api_url, path.lstrip("/"))
        if params:
            url += ("?" if "?" not in url else "&") + urlencode(params)
        request = Request(url, data=data, method=method.upper())
        for key, value in self._build_headers(headers).items():
            request.add_header(key, value)

        LOGGER.debug("GitHub API %s %s", method, url)
        try:
            with urlopen(request) as response:
                content_type = response.headers.get("Content-Type", "")
                payload = response.read()
                if content_type.startswith("application/json") or payload.startswith(b"{"):
                    return json.loads(payload.decode("utf-8"))
                return {"raw": payload}
        except HTTPError as exc:
            try:
                error_body = exc.read().decode("utf-8")
                parsed = json.loads(error_body) if error_body else {}
            except Exception:  # noqa: BLE001 - хочется показать исходную ошибку
                parsed = {}
            raise GitHubAPIError(status=exc.code, message=str(exc), response=parsed) from exc

    def list_releases(self, owner: str, repo: str, per_page: int = 30) -> Dict[str, Any]:
        return self._request("GET", f"repos/{owner}/{repo}/releases", params={"per_page": per_page})

    def get_release_by_tag(self, owner: str, repo: str, tag: str) -> Optional[Dict[str, Any]]:
        try:
            return self._request("GET", f"repos/{owner}/{repo}/releases/tags/{tag}")
        except GitHubAPIError as error:
            if error.status == 404:
                return None
            raise

    def create_release(
        self,
        owner: str,
        repo: str,
        *,
        tag_name: str,
        target_commitish: str,
        name: str,
        body: str,
        draft: bool = False,
        prerelease: bool = False,
    ) -> Dict[str, Any]:
        payload = {
            "tag_name": tag_name,
            "target_commitish": target_commitish,
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease,
        }
        return self._request("POST", f"repos/{owner}/{repo}/releases", data=json.dumps(payload).encode("utf-8"))

    def upload_asset(self, upload_url: str, asset_path: str, content_type: str) -> Dict[str, Any]:
        from pathlib import Path

        asset_file = Path(asset_path)
        if not asset_file.exists():
            raise FileNotFoundError(f"Файл {asset_path} не найден")

        upload_endpoint = upload_url.split("{", 1)[0]
        params = {"name": asset_file.name}
        with asset_file.open("rb") as stream:
            payload = stream.read()
        headers = {"Content-Type": content_type}
        return self._request(
            "POST",
            upload_endpoint,
            params=params,
            data=payload,
            headers=headers,
            raw_url=True,
        )

