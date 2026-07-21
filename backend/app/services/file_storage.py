import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import settings


class FileStorage(ABC):
    @abstractmethod
    def save(self, filename: str, content: bytes) -> str:
        """Persist the file and return a URL it can be retrieved from."""


class LocalFileStorage(FileStorage):
    """Stores files on local disk, served back via a static file mount.

    Stand-in for a real object store (S3 or similar) - swap in a different
    FileStorage implementation later without touching any endpoint that
    calls .save().
    """

    def __init__(self, base_dir: Path, base_url: str):
        self.base_dir = base_dir
        self.base_url = base_url.rstrip("/")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, filename: str, content: bytes) -> str:
        stored_name = f"{uuid.uuid4()}_{filename}"
        (self.base_dir / stored_name).write_bytes(content)
        return f"{self.base_url}/{stored_name}"


storage: FileStorage = LocalFileStorage(
    base_dir=Path(settings.upload_dir), base_url="/files"
)
