from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers import (
    costing,
    design_requests,
    fulfillment,
    projects,
    reference_data,
    tasks,
    users,
)

app = FastAPI(title="Claudie Workflow API")

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(design_requests.router)
app.include_router(tasks.router)
app.include_router(reference_data.router)
app.include_router(costing.router)
app.include_router(fulfillment.router)


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
