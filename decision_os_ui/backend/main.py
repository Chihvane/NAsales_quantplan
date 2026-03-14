from __future__ import annotations

from fastapi import FastAPI

from decision_os_ui.backend.api_routes import router
from decision_os_ui.backend.database import init_db


app = FastAPI(title="Decision OS API", version="0.1.0")
app.include_router(router)


@app.on_event("startup")
def startup() -> None:  # pragma: no cover
    init_db()
