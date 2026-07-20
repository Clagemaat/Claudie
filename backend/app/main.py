from fastapi import FastAPI

from app.routers import design_requests, projects, tasks, users

app = FastAPI(title="Claudie Workflow API")

app.include_router(users.router)
app.include_router(projects.router)
app.include_router(design_requests.router)
app.include_router(tasks.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
