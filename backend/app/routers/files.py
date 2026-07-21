from fastapi import APIRouter, File, UploadFile

from app.services.file_storage import storage

router = APIRouter(tags=["files"])


@router.post("/uploads")
async def upload_file(file: UploadFile = File(...)) -> dict:
    """Generic file upload, not tied to any specific entity - returns a URL
    that can be used anywhere the API expects one (e.g. a TemplateVersion's
    pdf_url), so the frontend can offer a real file picker instead of asking
    someone to paste a link."""
    content = await file.read()
    url = storage.save(file.filename, content)
    return {"url": url}
