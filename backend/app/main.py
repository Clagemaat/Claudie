import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.demo_auth import DemoBasicAuthMiddleware
from app.routers import (
    costing,
    design_requests,
    files,
    fulfillment,
    ops,
    projects,
    reference_data,
    tasks,
    users,
)

app = FastAPI(title="Claudie Workflow API")

# No per-user auth exists yet (see app.session in the frontend - it's a
# "pick your user" switcher, not real login). If DEMO_PASSWORD is set,
# gate the whole app behind one shared HTTP Basic credential so a public
# deployment isn't wide open to anyone who finds the URL. Unset locally,
# so dev is unaffected.
demo_password = os.environ.get("DEMO_PASSWORD")
if demo_password:
    app.add_middleware(
        DemoBasicAuthMiddleware,
        username=os.environ.get("DEMO_USERNAME", "claudie"),
        password=demo_password,
    )

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
app.include_router(files.router)

# Uploaded reference materials (see app.services.file_storage) are served
# back from here - swap for a real object store URL scheme later.
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=settings.upload_dir), name="files")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# In production, the frontend's build output is copied alongside this
# package (see Dockerfile) and served from the same origin as the API -
# no CORS, no separate static host needed. Locally, that directory
# doesn't exist (the frontend runs via its own Vite dev server instead),
# so "/" just points at the API docs as before.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")
