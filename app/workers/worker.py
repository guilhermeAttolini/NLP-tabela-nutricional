from __future__ import annotations
import time, json, os
from pathlib import Path
from .. import storage
from ..pipeline.parse import to_plain_text
from ..pipeline.extract import extract as extract_regex
from ..pipeline.nutrition import load_tbca, load_densidades, compute_nutrition
from ..pipeline.render import render_png, png_to_pdf
from ..pipeline.render_anvisa import render_anvisa_png
from ..pipeline.render_anvisa_vector import render_anvisa_vector_pdf

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TBCA_PATH = DATA_DIR / "tbca.csv"
DENS_PATH = DATA_DIR / "densidades.csv"

def choose_extractor(payload: dict):
    mode = (payload.get("extractor") or "auto").lower()
    if mode == "regex":
        return extract_regex
    if mode == "llm":
        try:
            from ..pipeline.extract_llm import extract_with_llm
            return lambda txt: extract_with_llm(txt)
        except Exception:
            return extract_regex
    if os.getenv("OPENAI_API_KEY"):
        try:
            from ..pipeline.extract_llm import extract_with_llm
            return lambda txt: extract_with_llm(txt)
        except Exception:
            pass
    return extract_regex

def process_job(job_id: str):
    job_dir = storage.JOBS_DIR / job_id
    input_payload = json.loads((job_dir / "input.json").read_text(encoding="utf-8"))
    storage.update_job(job_id, status="processing", message="Parsing input...")
    text = to_plain_text(input_payload.get("input_type", "auto"), input_payload["content"])

    extractor = choose_extractor(input_payload)
    storage.update_job(job_id, message=f"Extracting ingredients via {'LLM' if extractor!=extract_regex else 'regex'}...")
    items = extractor(text)

    storage.update_job(job_id, message="Computing nutrition...")
    tbca_df = load_tbca(str(TBCA_PATH)) if TBCA_PATH.exists() else None
    dens_df = load_densidades(str(DENS_PATH)) if DENS_PATH.exists() else None
    if tbca_df is None or dens_df is None:
        raise RuntimeError("Bases não encontradas em app/data (tbca.csv, densidades.csv).")

    summary = compute_nutrition(items, tbca_df, dens_df)

    results_dir = job_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    label_format = (input_payload.get("label_format") or "anvisa").lower()
    png_path = results_dir / "label.png"
    pdf_path = results_dir / "label.pdf"
    if label_format == "anvisa":
        render_anvisa_png(summary, png_path)
        render_anvisa_vector_pdf(summary, str(pdf_path))
    else:
        render_png(summary, png_path)
        png_to_pdf(png_path, pdf_path)

    storage.update_job(job_id, status="done", message="OK", results={
        "summary_json": f"/files/{job_id}/results/summary.json",
        "label_png": f"/files/{job_id}/results/label.png",
        "label_pdf": f"/files/{job_id}/results/label.pdf",
    })

def main():
    print("Worker started. Watching for queued jobs...")
    while True:
        try:
            queued = storage.list_queued_jobs()
            for job_id in queued:
                try:
                    process_job(job_id)
                except Exception as e:
                    storage.update_job(job_id, status="error", message=str(e))
        except Exception as e:
            print("Worker loop error:", e)
        time.sleep(2)

if __name__ == "__main__":
    main()
