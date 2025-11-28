from __future__ import annotations
import pandas as pd
from rapidfuzz import process, fuzz
from typing import List, Dict, Tuple

def load_tbca(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, sep=";", encoding="utf-8", engine="python", na_filter=False)
    except Exception:
        df = pd.read_csv(path, sep=";", encoding="latin1", engine="python", na_filter=False)

    RENAME_MAP_TBCA = {
        "codigo": "codigo",
        "nome": "descricao",
        "categoria": "categoria",
        "energia (kcal)": "kcal_100g",
        "carboidrato disponível (g)": "carbs_g_100g",
        "proteína (g)": "protein_g_100g",
        "lipídios (g)": "fat_g_100g",
        "ácidos graxos saturados (g)": "saturated_fat_g_100g",
        "ácidos graxos trans (g)": "trans_fat_g_100g",
        "fibra alimentar (g)": "fiber_g_100g",
        "sódio (mg)": "sodium_mg_100g",
        "açúcar de adição (g)": "sugar_g_100g",
    }

    rename_map = {}
    for col in df.columns:
        l = str(col).strip().lower()
        if l in RENAME_MAP_TBCA:
            rename_map[col] = RENAME_MAP_TBCA[l]

    df = df.rename(columns=rename_map)

    required_cols = [
        "descricao", "kcal_100g", "protein_g_100g", "fat_g_100g", "carbs_g_100g", 
        "sodium_mg_100g", "fiber_g_100g", "saturated_fat_g_100g", "trans_fat_g_100g", "sugar_g_100g"
    ]

    for c in required_cols:
        if c not in df.columns:
            df[c] = 0      

    for c in required_cols[1:]:
        df[c] = (
            df[c].astype(str)
                .str.replace(",", ".", regex=False)
        )
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    df["descricao"] = df["descricao"].astype(str)
    df["descricao_norm"] = df["descricao"].str.lower().str.strip()
    return df

def load_densidades(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, sep=",", encoding="utf-8", na_filter=False)
    except Exception:
        df = pd.read_csv(path, sep=",", encoding="latin1", na_filter=False)

    rename_map = {}
    for col in df.columns:
        l = str(col).strip().lower()
        if l.startswith("ingred"):
            rename_map[col] = "ingrediente"
        elif "medida" in l:
            rename_map[col] = "medida_caseira"
        elif "grama" in l:
            rename_map[col] = "gramas"
    df = df.rename(columns=rename_map)

    for c in ["ingrediente", "medida_caseira", "gramas"]:
        if c not in df.columns:
            df[c] = "" if c != "gramas" else 0

    df["ingrediente"] = df["ingrediente"].astype(str)
    df["ingrediente_norm"] = df["ingrediente"].str.lower().str.strip()
    df["medida_caseira"] = df["medida_caseira"].astype(str).str.lower().str.strip()
    df["gramas"] = (
        df["gramas"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    )
    df["gramas"] = pd.to_numeric(df["gramas"], errors="coerce").fillna(0.0)

    return df

UNIT_TO_G = {"g": 1.0, "kg": 1000.0}
UNIT_TO_ML = {"ml": 1.0, "l": 1000.0}
CASEIRAS = {"xic", "colher_sopa", "colher_cha", "pitada"}
VOLUME_UNITS = {"ml", "l"} | CASEIRAS
UNIT_ALIASES = {"unidade": "un", "un": "un"}
DEFAULT_UNIT_WEIGHTS = {"colher_sopa": 15.0, "colher_cha": 5.0, "xic": 240.0, "pitada": 1.0}

def best_match(name: str, choices: List[str]) -> Tuple[str, float]:
    res = process.extractOne(name, choices, scorer=fuzz.WRatio)
    if res:
        return res[0], float(res[1])
    return ("", 0.0)

def to_grams(qty: float, unit: str, name: str, dens_df: pd.DataFrame) -> float:
    unit = UNIT_ALIASES.get(unit, unit)
    name_norm = name.lower().strip()

    if unit in UNIT_TO_G:
        return qty * UNIT_TO_G[unit]

    if unit in CASEIRAS and {"ingrediente_norm", "medida_caseira", "gramas"}.issubset(set(dens_df.columns)):
        if len(dens_df):
            target, score = best_match(name_norm, dens_df["ingrediente_norm"].tolist())
        else:
            target, score = ("", 0.0)
        if score >= 80:
            rows = dens_df[(dens_df["ingrediente_norm"] == target) & (dens_df["medida_caseira"] == unit)]
            if not rows.empty:
                grams_per_unit = float(rows.iloc[0]["gramas"])
                if grams_per_unit > 0:
                    return qty * grams_per_unit

    if unit in {"ml", "l"}:
        ml = qty * UNIT_TO_ML.get(unit, 1.0)
        return ml * 1.0

    if unit in CASEIRAS:
        ml = qty * DEFAULT_UNIT_WEIGHTS.get(unit, 1.0)
        return ml * 1.0

    return qty * 30.0

def compute_nutrition(items: List[Dict], tbca_df: pd.DataFrame, dens_df: pd.DataFrame) -> Dict:
    out_items = []
    total_kcal = total_p = total_f = total_c = total_na = 0.0
    total_fib = total_sat = total_trans = total_sug = 0.0

    for it in items:
        name = it["name"]
        grams = to_grams(float(it["quantity"]), it["unit"], name, dens_df)

        target, score = best_match(name.lower(), tbca_df["descricao_norm"].tolist())
        row = None
        if target and (tbca_df["descricao_norm"] == target).any():
            row = tbca_df.loc[tbca_df["descricao_norm"] == target].iloc[0]

        def get_val(col):
            # Verifica se a coluna existe e se a linha foi encontrada
            if row is None or col not in row: return 0.0
            # A verificação de tipo (float(row[col])) é importante para o cálculo, 
            # mas como já fizemos o to_numeric no load_tbca, a conversão deve ser segura.
            return float(row[col]) * grams / 100

        # Cálculo dos nutrientes
        kcal = get_val("kcal_100g")
        p = get_val("protein_g_100g")
        f = get_val("fat_g_100g")
        c = get_val("carbs_g_100g")
        na = get_val("sodium_mg_100g")
        
        # NOVOS CÁLCULOS
        fib = get_val("fiber_g_100g")
        sat = get_val("saturated_fat_g_100g")
        trans = get_val("trans_fat_g_100g")
        sug = get_val("sugar_g_100g")

        total_kcal += kcal; total_p += p; total_f += f; total_c += c; total_na += na
        total_fib += fib; total_sat += sat; total_trans += trans; total_sug += sug
        out_items.append({
            "name": name, "amount_g": grams, "mapping": (row["descricao"] if row is not None else None),
            "kcal": kcal, "protein_g": p, "fat_g": f, "carbs_g": c, "sodium_mg": na,
            "fiber_g": fib, "saturated_fat_g": sat, "trans_fat_g": trans, "sugar_g": sug # NOVOS CAMPOS
        })

    return {
        "total_kcal": total_kcal,
        "protein_g": total_p,
        "fat_g": total_f,
        "carbs_g": total_c,
        "sodium_mg": total_na,
        "fiber_g": total_fib,          
        "saturated_fat_g": total_sat,   
        "trans_fat_g": total_trans,     
        "sugar_g": total_sug,           
        "per_serving": None,
        "items": out_items
    }
