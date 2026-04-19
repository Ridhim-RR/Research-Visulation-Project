# Research-Visulation-Project

## Backend Setup (FastAPI)

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

1. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

1. Start the API server:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

1. Verify the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Frontend Setup (Vite)

1. Install frontend dependencies:

```bash
cd frontend
npm install
```

1. Run the Vite dev server:

```bash
npm run dev
```

Open the frontend at:

```bash
http://127.0.0.1:5173/
```

Vite proxies `/api` and `/health` to FastAPI on port 8000.

## Production Frontend Build

1. Build the frontend for FastAPI to serve:

```bash
cd frontend
npm run build
```

1. Start FastAPI and open:

```bash
http://127.0.0.1:8000/
```

## Frontend Scope

The current frontend is intentionally minimal:

1. upload a MAT file
2. send it to the FastAPI visualization endpoint
3. show the returned Semani figures in the browser

## EEG Semani Processing API

### 1) Process uploaded MAT file

- Method: POST
- Route: /api/eeg/semani/process
- Content-Type: multipart/form-data
- Required file field: file
- Optional form fields with defaults:
	- fs=512
	- twndw=1.0
	- frame_index=1
	- nj=8
	- freq_max_hz=64.0
	- img_n=900

Example:

```bash
curl -X POST "http://127.0.0.1:8000/api/eeg/semani/process" \
	-F "file=@eegd2data.mat" \
	-F "fs=512" \
	-F "twndw=1" \
	-F "frame_index=1" \
	-F "nj=8" \
	-F "freq_max_hz=64" \
	-F "img_n=900"
```

### 2) Process the built-in sample MAT file

- Method: GET
- Route: /api/eeg/semani/sample

Example:

```bash
curl "http://127.0.0.1:8000/api/eeg/semani/sample"
```

### Response summary

The API returns:

- metadata (shape and processing info)
- settings (effective settings used)
- numeric (time/frequency/polar matrices)
- images (base64 PNG strings for:
	- semaniFigurePngBase64
	- channelsFigurePngBase64)
