from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .eeg_processing import ProcessingSettings, process_eeg_mat_bytes

app = FastAPI(title="Research Visualization Backend")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
if FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST_DIR / "assets"), name="assets")


@app.get("/", responses={404: {"description": "Frontend index not found"}})
def serve_frontend() -> FileResponse:
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Frontend build not found. Run: cd frontend && npm run build",
        )
    return FileResponse(index_file)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/eeg/semani/process",
    responses={
        400: {"description": "Invalid MAT file or processing settings"},
        500: {"description": "Unexpected processing error"},
    },
)
async def process_eeg_semani(
    file: Annotated[UploadFile, File(...)],
    fs: Annotated[int, Form()] = 512,
    twndw: Annotated[float, Form()] = 1.0,
    frame_index: Annotated[int, Form()] = 1,
    nj: Annotated[int, Form()] = 8,
    freq_max_hz: Annotated[float, Form()] = 64.0,
    img_n: Annotated[int, Form()] = 900,
) -> dict:
    settings = ProcessingSettings(
        fs=fs,
        twndw=twndw,
        frame_index=frame_index,
        nj=nj,
        freq_max_hz=freq_max_hz,
        img_n=img_n,
    )

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        return process_eeg_mat_bytes(file_bytes=file_bytes, settings=settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Unexpected processing error: {exc}") from exc


@app.get(
    "/api/eeg/semani/sample",
    responses={
        400: {"description": "Invalid processing settings"},
        404: {"description": "Sample MAT file not found"},
        500: {"description": "Unexpected processing error"},
    },
)
def process_sample_data(
    fs: int = 512,
    twndw: float = 1.0,
    frame_index: int = 1,
    nj: int = 8,
    freq_max_hz: float = 64.0,
    img_n: int = 900,
) -> dict:
    settings = ProcessingSettings(
        fs=fs,
        twndw=twndw,
        frame_index=frame_index,
        nj=nj,
        freq_max_hz=freq_max_hz,
        img_n=img_n,
    )

    sample_path = Path(__file__).resolve().parent.parent / "eegd2data.mat"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample file eegd2data.mat was not found.")

    try:
        file_bytes = sample_path.read_bytes()
        return process_eeg_mat_bytes(file_bytes=file_bytes, settings=settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Unexpected processing error: {exc}") from exc
