from __future__ import annotations
import re
from typing import List, Dict

UNIT_MAP = {
    r"x[ií]cara(s)?": "xic",
    r"colher(es)?(\s*\(de\s*sopa\)|\s*de\s*sopa)?": "colher_sopa",
    r"colher(es)?(\s*\(de\s*ch[aá]\)|\s*de\s*ch[aá])?": "colher_cha",
    r"pitada(s)?": "pitada",
    r"g(r|ramas)?": "g",
    r"kg": "g",
    r"ml": "ml",
    r"l(itro)?s?": "ml",
    r"unidade(s)?|un\.?": "un",
    r"sache(s)?|sach[eê]": "un",
    r"dente(s)?": "un",
    r"lata(s)?": "un",
    r"x": "un",
}
UNIT_PATTERNS = [(re.compile(pat, re.I), out) for pat, out in UNIT_MAP.items()]
FRACTION_PAT = re.compile(r"(\d+)\\s*/\\s*(\\d+)")
NUMBER_PAT = re.compile(r"(?<!\\w)(\\d+(?:[.,]\\d+)?)(?!\\w)")

def _to_float(token: str) -> float:
    token = token.strip().replace(",", ".")
    m = FRACTION_PAT.fullmatch(token)
    if m:
        return float(m.group(1)) / float(m.group(2))
    try:
        return float(token)
    except:
        return 0.0

def _norm_unit(u: str) -> str:
    for pat, out in UNIT_PATTERNS:
        if pat.fullmatch(u.strip()):
            return out
    return u.lower().strip()

def extract_ingredients_lines(text: str) -> List[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    results = []
    unit_keywords = ["xíc", "colher", "g", "kg", "ml", "l", "pitada", "dente", "lata", "sach"]
    for ln in lines:
        low = ln.lower()
        if any(k in low for k in unit_keywords) or NUMBER_PAT.search(ln):
            results.append(ln)
    return results

def parse_line(line: str) -> Dict:
    tokens = line.split()
    qty = 0.0
    unit = "un"
    rest = line
    m = FRACTION_PAT.match(tokens[0]) if tokens else None
    if tokens and (NUMBER_PAT.match(tokens[0]) or m):
        qty = _to_float(tokens[0].replace(",", "."))
        rest = line[len(tokens[0]):].strip()
    if rest:
        m2 = re.match(r"^([A-Za-zÀ-ÿ]+(?:\\s*\\([^)]+\\))?)", rest)
        if m2:
            unit = _norm_unit(m2.group(1))
            rest = rest[m2.end():].strip(", .-")
    rest = re.sub(r"^(de|da|do|das|dos)\\s+", "", rest, flags=re.I)
    name = rest.strip()
    return {"name": name, "quantity": float(qty or 1), "unit": unit}

def extract(text: str) -> List[Dict]:
    lines = extract_ingredients_lines(text)
    items = [parse_line(ln) for ln in lines if ln]
    items = [it for it in items if it["name"]]
    return items
