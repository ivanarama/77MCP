"""Unified Starlette application: web UI + MCP SSE transport."""

from __future__ import annotations

import os
import traceback

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Mount, Route

from . import tools
from .server import mcp

DATA_DIR = os.environ.get("MCP_DATA_DIR", "/data")
MD_FILENAME = "1cv7.md"

HTML_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>1C 7.7 Metadata MCP Server</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f5f5f5; color: #333; min-height: 100vh;
    display: flex; flex-direction: column; align-items: center;
    padding: 2rem 1rem;
  }
  h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
  .subtitle { color: #666; margin-bottom: 2rem; font-size: 0.9rem; }
  .card {
    background: #fff; border-radius: 12px; padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08); width: 100%; max-width: 600px;
    margin-bottom: 1.5rem;
  }
  .drop-zone {
    border: 2px dashed #ccc; border-radius: 8px; padding: 3rem 1rem;
    text-align: center; cursor: pointer; transition: all 0.2s;
    color: #888;
  }
  .drop-zone.dragover { border-color: #4a90d9; background: #eef4fc; color: #4a90d9; }
  .drop-zone.uploading { border-color: #f0ad4e; color: #f0ad4e; }
  .drop-zone.success { border-color: #5cb85c; color: #5cb85c; }
  .drop-zone.error { border-color: #d9534f; color: #d9534f; }
  .drop-zone p { margin: 0.5rem 0; }
  .drop-zone .icon { font-size: 2.5rem; }
  .drop-zone input[type=file] { display: none; }
  .progress-bar {
    height: 4px; background: #e0e0e0; border-radius: 2px;
    margin-top: 1rem; overflow: hidden; display: none;
  }
  .progress-bar .fill {
    height: 100%; background: #4a90d9; width: 0%;
    transition: width 0.3s;
  }
  .status { margin-top: 1rem; }
  .status h3 { font-size: 1.1rem; margin-bottom: 0.75rem; color: #333; }
  .status-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  .status-item {
    display: flex; justify-content: space-between;
    padding: 0.4rem 0; border-bottom: 1px solid #f0f0f0;
  }
  .status-item .label { color: #888; }
  .status-item .value { font-weight: 600; }
  .btn {
    display: inline-block; padding: 0.5rem 1.25rem; border: none;
    border-radius: 6px; cursor: pointer; font-size: 0.9rem;
    background: #4a90d9; color: #fff; margin-top: 1rem;
    transition: background 0.2s;
  }
  .btn:hover { background: #3a7bc8; }
  .btn:disabled { background: #ccc; cursor: not-allowed; }
  .connection-info {
    font-size: 0.85rem; color: #666; margin-top: 0.5rem;
  }
  .connection-info code {
    background: #f0f0f0; padding: 0.15rem 0.4rem; border-radius: 3px;
    font-size: 0.8rem;
  }
  #config-info { display: none; }
</style>
</head>
<body>

<h1>1C 7.7 Metadata MCP Server</h1>
<p class="subtitle">Upload 1Cv7.MD configuration file to start</p>

<div class="card">
  <div class="drop-zone" id="dropZone">
    <div class="icon">&#128194;</div>
    <p><strong>Drag & drop 1Cv7.MD here</strong></p>
    <p>or click to select file</p>
    <input type="file" id="fileInput" accept=".md,.MD">
  </div>
  <div class="progress-bar" id="progressBar">
    <div class="fill" id="progressFill"></div>
  </div>
  <div id="uploadMsg" style="margin-top:0.75rem; text-align:center; font-size:0.9rem;"></div>
</div>

<div class="card" id="config-info">
  <div class="status">
    <h3>Loaded Configuration</h3>
    <div id="configName" style="font-size:1.1rem; font-weight:600; margin-bottom:0.5rem;"></div>
    <div id="configVersion" style="color:#666; margin-bottom:1rem;"></div>
    <div class="status-grid" id="statusGrid"></div>
    <button class="btn" id="reloadBtn" onclick="reloadConfig()">Reload</button>
  </div>
</div>

<div class="card">
  <div class="connection-info">
    <strong>MCP SSE Endpoint:</strong><br>
    <code id="sseUrl"></code>
    <p style="margin-top:0.5rem;">Claude Code:</p>
    <code>claude mcp add --transport sse 1c77-metadata <span id="sseUrlCmd"></span></code>
  </div>
</div>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const uploadMsg = document.getElementById('uploadMsg');
const configInfo = document.getElementById('config-info');

const baseUrl = window.location.origin;
document.getElementById('sseUrl').textContent = baseUrl + '/sse';
document.getElementById('sseUrlCmd').textContent = baseUrl + '/sse';

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
});

function uploadFile(file) {
  dropZone.className = 'drop-zone uploading';
  dropZone.querySelector('.icon').textContent = '\\u23F3';
  dropZone.querySelector('p').textContent = 'Uploading...';
  progressBar.style.display = 'block';
  progressFill.style.width = '0%';
  uploadMsg.textContent = '';

  const formData = new FormData();
  formData.append('file', file);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/upload');

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      progressFill.style.width = Math.round(e.loaded / e.total * 100) + '%';
    }
  };

  xhr.onload = () => {
    progressFill.style.width = '100%';
    try {
      const resp = JSON.parse(xhr.responseText);
      if (xhr.status === 200 && resp.ok) {
        dropZone.className = 'drop-zone success';
        dropZone.querySelector('.icon').textContent = '\\u2705';
        dropZone.querySelector('p').textContent = 'Configuration loaded!';
        uploadMsg.textContent = '';
        loadStatus();
      } else {
        dropZone.className = 'drop-zone error';
        dropZone.querySelector('.icon').textContent = '\\u274C';
        dropZone.querySelector('p').textContent = 'Upload failed';
        uploadMsg.textContent = resp.error || 'Unknown error';
        uploadMsg.style.color = '#d9534f';
      }
    } catch {
      dropZone.className = 'drop-zone error';
      dropZone.querySelector('.icon').textContent = '\\u274C';
      dropZone.querySelector('p').textContent = 'Upload failed';
      uploadMsg.textContent = xhr.responseText;
      uploadMsg.style.color = '#d9534f';
    }
  };

  xhr.onerror = () => {
    dropZone.className = 'drop-zone error';
    dropZone.querySelector('.icon').textContent = '\\u274C';
    dropZone.querySelector('p').textContent = 'Network error';
    uploadMsg.style.color = '#d9534f';
  };

  xhr.send(formData);
}

function loadStatus() {
  fetch('/api/status')
    .then(r => r.json())
    .then(data => {
      if (!data.loaded) { configInfo.style.display = 'none'; return; }
      configInfo.style.display = 'block';
      document.getElementById('configName').textContent = data.name || 'Unnamed';
      document.getElementById('configVersion').textContent = 'Version: ' + (data.version || '-');
      const grid = document.getElementById('statusGrid');
      grid.innerHTML = '';
      const items = [
        ['Constants', data.counts.constants],
        ['Catalogs', data.counts.catalogs],
        ['Documents', data.counts.documents],
        ['Registers', data.counts.registers],
        ['Enums', data.counts.enums],
        ['Reports', data.counts.reports],
        ['Journals', data.counts.journals],
        ['CalcVars', data.counts.calc_vars],
      ];
      for (const [label, val] of items) {
        grid.innerHTML += '<div class="status-item"><span class="label">'
          + label + '</span><span class="value">' + val + '</span></div>';
      }
    });
}

function reloadConfig() {
  const btn = document.getElementById('reloadBtn');
  btn.disabled = true;
  btn.textContent = 'Reloading...';
  fetch('/upload', { method: 'POST', body: new FormData() })
    .then(r => r.json())
    .then(data => {
      btn.disabled = false;
      btn.textContent = 'Reload';
      if (data.ok) loadStatus();
      else { uploadMsg.textContent = data.error; uploadMsg.style.color = '#d9534f'; }
    })
    .catch(() => { btn.disabled = false; btn.textContent = 'Reload'; });
}

// Check status on page load
loadStatus();
</script>
</body>
</html>"""


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
        },
    })


async def startup() -> None:
    """Try to load existing configuration on startup."""
    md_path = os.path.join(DATA_DIR, MD_FILENAME)
    if os.path.exists(md_path):
        try:
            tools.init(md_path)
            print(f"Auto-loaded configuration from {md_path}")
        except Exception as e:
            print(f"Failed to auto-load {md_path}: {e}")


# Build the unified ASGI app
mcp_sse_app = mcp.sse_app()

app = Starlette(
    routes=[
        Route("/", upload_page),
        Route("/upload", handle_upload, methods=["POST"]),
        Route("/api/status", api_status),
        Mount("/", app=mcp_sse_app),
    ],
    on_startup=[startup],
)
