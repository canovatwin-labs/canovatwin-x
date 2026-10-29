"""Serve the locally built panel without exposing arbitrary package files."""

import re
from pathlib import Path

from fastapi import FastAPI
from starlette.responses import FileResponse, RedirectResponse

from .boundary import APIProblem

WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
ASSET_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
ASSET_TYPES = {
    ".js": "text/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
}
PANEL_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; img-src 'self'; font-src 'self'; "
        "base-uri 'none'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
    ),
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def _bundle_file(relative: str) -> Path | None:
    root = WEB_ROOT.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        return None
    return path


def register_panel(app: FastAPI) -> None:
    """Public shell; all data and mutations continue to require API credentials."""

    @app.api_route("/panel", methods=["GET", "HEAD"], include_in_schema=False)
    def panel_redirect():
        return RedirectResponse("/panel/", status_code=308, headers=PANEL_HEADERS)

    @app.api_route("/panel/", methods=["GET", "HEAD"], include_in_schema=False)
    def panel_index():
        path = _bundle_file("index.html")
        if path is None:
            raise APIProblem(
                503, "PANEL_NOT_BUILT", "The local panel bundle is unavailable", headers=PANEL_HEADERS
            )
        return FileResponse(path, media_type="text/html", headers=PANEL_HEADERS)

    @app.api_route("/panel/assets/{name:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def panel_asset(name: str):
        media_type = ASSET_TYPES.get(Path(name).suffix)
        path = _bundle_file(f"assets/{name}") if ASSET_NAME.fullmatch(name) and media_type else None
        if path is None:
            raise APIProblem(404, "HTTP_404", "Panel asset was not found", headers=PANEL_HEADERS)
        return FileResponse(path, media_type=media_type, headers=PANEL_HEADERS)
