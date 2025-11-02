# Nutri Label Service (Python, FastAPI + Worker + LLM + ANVISA)

API que recebe texto/HTML/URL, cria um *job* e retorna um `job_id`.  
Um *worker* processa: **parse → extração (regex/LLM) → mapeamento TBCA/densidades → rótulo ANVISA (PNG/PDF)**.

## Rodar (dev)
```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt

# Terminal 1: API
uvicorn app.main:app --reload

# Terminal 2: Worker
python -m app.workers.worker
```

## Env LLM
```bash
export OPENAI_API_KEY=SEU_TOKEN
export OPENAI_MODEL=gpt-4o-mini  # opcional
```

## Endpoints
- `POST /v1/jobs` → cria job. Payload:
  ```json
  {"input_type":"auto|text|html|url","content":"...","extractor":"auto|regex|llm","label_format":"anvisa|simple"}
  ```
- `GET /v1/jobs/{job_id}` → status + links quando pronto.
- `GET /v1/jobs/{job_id}/results/{fname}` → `summary.json`, `label.png`, `label.pdf`.
