from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import JobCreate, JobStatus
from . import storage
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
import os, json

app = FastAPI(title="Nutri Label Service", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Altere para os domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = Path(os.getenv("JOBS_DIR", Path(__file__).resolve().parents[1] / "jobs"))
storage.ensure_dirs()
app.mount("/files", StaticFiles(directory=str(JOBS_DIR)), name="files")

@app.post("/v1/jobs", response_model=JobStatus)
def create_job(job: JobCreate):
    job_id = storage.create_job(job.model_dump())
    status = storage.get_job(job_id)
    return status

@app.get("/v1/jobs/{job_id}", response_model=JobStatus)
def get_job(job_id: str):
    status = storage.get_job(job_id)
    if not status:
        raise HTTPException(404, "Job not found")
    if status.get("status") == "done":
        base = f"/files/{job_id}/results"
        status.setdefault("results", {})
        status["results"]["summary_json"] = f"{base}/summary.json"
        status["results"]["label_png"] = f"{base}/label.png"
        status["results"]["label_pdf"] = f"{base}/label.pdf"
    return status

@app.get("/v1/jobs/{job_id}/results/{fname}")
def get_result_file(job_id: str, fname: str):
    path = JOBS_DIR / job_id / "results" / fname
    if not path.exists():
        raise HTTPException(404, "Result not found")
    return FileResponse(path)
