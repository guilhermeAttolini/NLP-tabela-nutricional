from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any
from pathlib import Path

DV = {
    "energy_kcal": 2000.0,
    "carbs_g": 300.0,
    "protein_g": 75.0,
    "fat_g": 55.0,
    "sat_fat_g": 22.0,
    "fiber_g": 25.0,
    "sodium_mg": 2000.0,
}

def _pct(val, dv):
    if dv <= 0:
        return None
    return max(0, (val / dv) * 100.0)

def _try_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def render_anvisa_png(summary: Dict[str, Any], out_path: Path, title="INFORMAÇÃO NUTRICIONAL", width=800, height=700):
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    font_title = _try_font(28)
    font_b = _try_font(20)
    font = _try_font(18)
    font_small = _try_font(14)

    d.rectangle([10, 10, width-10, height-10], outline="black", width=6)
    y = 20
    d.text((20, y), title, font=font_title, fill="black"); y += 40
    d.line([(20, y), (width-20, y)], fill="black", width=3); y += 10

    d.text((20, y), "Porção: receita inteira (estimada)", font=font_b, fill="black"); y += 30
    d.line([(20, y), (width-20, y)], fill="black", width=2); y += 10

    energy = float(summary.get("total_kcal", 0.0))
    carbs = float(summary.get("carbs_g", summary.get("carbs_g", 0.0)))
    protein = float(summary.get("protein_g", 0.0))
    fat = float(summary.get("fat_g", 0.0))
    sodium_mg = float(summary.get("sodium_mg", 0.0))

    def row(label_left, qty_str, vd_str):
        nonlocal y
        d.text((30, y), label_left, font=font, fill="black")
        d.text((width-300, y), f"Quant. por porção: {qty_str}", font=font, fill="black")
        d.text((width-160, y), f"%VD*: {vd_str}", font=font, fill="black")
        y += 26

    row("Valor energético", f"{energy:.0f} kcal", f"{_pct(energy, DV['energy_kcal']):.0f}%")
    row("Carboidratos",    f"{carbs:.1f} g", f"{_pct(carbs, DV['carbs_g']):.0f}%")
    row("Proteínas",       f"{protein:.1f} g", f"{_pct(protein, DV['protein_g']):.0f}%")
    row("Gorduras totais", f"{fat:.1f} g", f"{_pct(fat, DV['fat_g']):.0f}%")
    row("Gorduras saturadas", "N/D", "N/D")
    row("Gorduras trans",  "N/D", "N/D")
    row("Fibra alimentar", "N/D", "N/D")
    row("Sódio",           f"{sodium_mg:.0f} mg", f"{_pct(sodium_mg, DV['sodium_mg']):.0f}%")

    y += 10
    d.line([(20, y), (width-20, y)], fill="black", width=2); y += 10

    obs = [
        "* % Valores Diários de referência com base em uma dieta de 2.000 kcal (8.400 kJ).",
        "  Seus valores diários podem ser maiores ou menores dependendo de suas necessidades energéticas.",
        "  Itens marcados como N/D não foram estimados nesta versão.",
    ]
    for line in obs:
        d.text((20, y), line, font=font_small, fill="black"); y += 20

    img.save(out_path)
