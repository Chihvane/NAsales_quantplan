from __future__ import annotations

from fastapi import FastAPI

from backend.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Decision OS", version="0.3.0")
    app.include_router(api_router)
    return app
