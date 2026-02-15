"""Entry point for running the server as `python -m mcp_1c77`."""

import uvicorn

from .web import app

uvicorn.run(app, host="0.0.0.0", port=8080)
