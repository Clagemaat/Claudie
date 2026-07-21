from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import (
    costing,
    design_requests,
    fulfillment,
    ops,
    projects,
    reference_data,
    tasks,
    users,
)

app = FastAPI(title="Claudie Workflow API")

# No auth exists yet, so this is permissive by design - an internal admin
# tool in a private dev environment. The frontend's Vite dev server proxies
# API calls same-origin anyway, so this is defensive/for direct access.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(design_requests.router)
app.include_router(tasks.router)
app.include_router(reference_data.router)
app.include_router(costing.router)
app.include_router(fulfillment.router)
app.include_router(ops.router)

# Uploaded reference materials (see app.services.file_storage) are served
# back from here - swap for a real object store URL scheme later.
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
