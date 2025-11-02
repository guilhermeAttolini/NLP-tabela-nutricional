
from __future__ import annotations
import os, json, re
from typing import List, Dict
from openai import OpenAI

SYSTEM = """Você extrai ingredientes de receitas em português do Brasil.
Responda APENAS com JSON válido e NADA mais, no formato:
{"items":[{"name":"...","quantity":1.0,"unit":"g","note":"opcional"}]}
Regras:
- 'name' no singular, sem marca.
- 'quantity' numérico (frações -> decimal).
- 'unit' ∈ {g, kg, ml, l, xic, colher_sopa, colher_cha, pitada, un}.
- Se não houver quantidade explícita: quantity=1, unit="un".
- Números com vírgula devem usar ponto.
- Não inclua modo de preparo, só ingredientes.
"""

USER_TMPL = """Texto de entrada:
```
{content}
```
Retorne SOMENTE o JSON pedido, sem explicações.
"""

def _client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não definido no ambiente.")
    return OpenAI(api_key=api_key)

def _extract_json_block(s: str) -> dict:
    try:
        return json.loads(s)
    except Exception:
        pass
    import re
    m = re.search(r"\\{.*\\}", s, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {"items": []}

def extract_with_llm(text: str) -> List[Dict]:
    client = _client()
    prompt = USER_TMPL.format(content=text[:8000])

    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": prompt},
        ],
    )
    out = resp.choices[0].message.content or ""
    data = _extract_json_block(out)
    items = data.get("items", [])

    cleaned = []
    for it in items:
        name = (it.get("name") or "").strip()
        if not name:
            continue
        try:
            qty = float(str(it.get("quantity", 1)).replace(",", "."))
        except Exception:
            qty = 1.0
        unit = (it.get("unit") or "un").strip().lower()
        note = (it.get("note") or None)
        cleaned.append({"name": name, "quantity": qty, "unit": unit, "note": note})
    return cleaned
