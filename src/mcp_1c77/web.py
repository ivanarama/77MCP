"""Unified Starlette application: web UI + MCP SSE transport."""

from __future__ import annotations

import os
import traceback

from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Mount, Route

from . import tools
from .server import mcp

DATA_DIR = os.environ.get("MCP_DATA_DIR", "/data")
MD_FILENAME = "1cv7.md"

_HTML_PAGE_PATH = Path(__file__).parent / "static" / "index.html"
HTML_PAGE = _HTML_PAGE_PATH.read_text(encoding="utf-8")



async def upload_page(request: Request) -> HTMLResponse:
    """Serve the upload page."""
    return HTMLResponse(HTML_PAGE)


async def handle_upload(request: Request) -> JSONResponse:
    """Handle file upload or reload of existing file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    md_path = os.path.join(DATA_DIR, MD_FILENAME)

    form = await request.form()
    uploaded = form.get("file")

    if uploaded is not None and hasattr(uploaded, "read"):
        contents = await uploaded.read()
        if not contents:
            # Empty file in form — try reloading existing
            if not os.path.exists(md_path):
                return JSONResponse({"ok": False, "error": "No file uploaded and no existing file to reload."})
        else:
            with open(md_path, "wb") as f:
                f.write(contents)
    else:
        # No file in request — reload existing
        if not os.path.exists(md_path):
            return JSONResponse({"ok": False, "error": "No file uploaded and no existing file to reload."})

    try:
        tools.init(md_path)
        config = tools.get_loader().config
        return JSONResponse({
            "ok": True,
            "name": config.name,
            "version": config.version,
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Parse error: {e}\n{traceback.format_exc()}"})


async def api_status(request: Request) -> JSONResponse:
    """Return current configuration status as JSON."""
    loader = tools.get_loader()
    if not loader.is_loaded:
        return JSONResponse({"loaded": False})

    config = loader.config
    coa_count = 1 if config.chart_of_accounts and config.chart_of_accounts.id else 0
    return JSONResponse({
        "loaded": True,
        "name": config.name,
        "version": config.version,
        "file_path": config.file_path,
        "counts": {
            "constants": len(config.constants),
            "catalogs": len(config.catalogs),
            "documents": len(config.documents),
            "registers": len(config.registers),
            "enums": len(config.enums),
            "reports": len(config.reports),
            "journals": len(config.journals),
            "calc_vars": len(config.calc_vars),
            "chart_of_accounts": coa_count,
        },
    })


async def startup() -> None:
    """Try to load existing configuration on startup."""
    os.makedirs(DATA_DIR, exist_ok=True)
    tools.set_data_dir(DATA_DIR)
    md_path = os.path.join(DATA_DIR, MD_FILENAME)
    if os.path.exists(md_path):
        try:
            tools.init(md_path)
            print(f"Auto-loaded configuration from {md_path}")
        except Exception as e:
            print(f"Failed to auto-load {md_path}: {e}")


# Build the unified ASGI app
mcp_sse_app = mcp.sse_app()


@asynccontextmanager
async def lifespan(app):
    await startup()
    yield


app = Starlette(
    routes=[
        Route("/", upload_page),
        Route("/upload", handle_upload, methods=["POST"]),
        Route("/api/status", api_status),
        Mount("/", app=mcp_sse_app),
    ],
    lifespan=lifespan,
)
