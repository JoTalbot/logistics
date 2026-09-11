from pathlib import Path
from fastapi.responses import FileResponse
from .api import app
from . import remote_control  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]

@app.get("/", include_in_schema=False)
def control_plane_home() -> FileResponse:
    return FileResponse(ROOT / "index.html")
