from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .eeg_processing import ProcessingSettings, process_eeg_mat_bytes

app = FastAPI(title="Research Visualization Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/eeg/semani/process")
async def process_eeg_semani(
    file: UploadFile = File(...),
    fs: int = Form(512),
    twndw: float = Form(1.0),
    frame_index: int = Form(1),
    nj: int = Form(8),
    freq_max_hz: float = Form(64.0),
    img_n: int = Form(900),
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


@app.get("/api/eeg/semani/sample")
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
