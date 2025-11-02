import json, time, uuid, os
from pathlib import Path
from typing import Dict, Any, List

JOBS_DIR = Path(os.getenv("JOBS_DIR", Path(__file__).resolve().parents[1] / "jobs"))
INDEX = JOBS_DIR / "index.json"

def _now() -> float:
    return time.time()

def ensure_dirs():
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        INDEX.write_text(json.dumps({}, ensure_ascii=False, indent=2), encoding="utf-8")

def _read_index() -> Dict[str, Any]:
    ensure_dirs()
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write_index(idx: Dict[str, Any]):
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

def create_job(payload: Dict[str, Any]) -> str:
    ensure_dirs()
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    (job_dir / "input.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    status = {
        "job_id": job_id,
        "status": "queued",
        "message": None,
        "created_at": _now(),
        "updated_at": _now(),
        "results": None,
    }
    (job_dir / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    idx = _read_index()
    idx[job_id] = status
    _write_index(idx)
    return job_id

def get_job(job_id: str) -> Dict[str, Any] | None:
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        return None
    try:
        return json.loads((job_dir / "status.json").read_text(encoding="utf-8"))
    except Exception:
        return None

def update_job(job_id: str, **kwargs):
    job_dir = JOBS_DIR / job_id
    status_path = job_dir / "status.json"
    idx = _read_index()

    if not status_path.exists():
        return

    status = json.loads(status_path.read_text(encoding="utf-8"))
    status.update(kwargs)
    status["updated_at"] = _now()
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    idx[job_id] = status
    _write_index(idx)

def list_queued_jobs() -> List[str]:
    idx = _read_index()
    return [k for k,v in idx.items() if v.get("status") == "queued"]
