from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def render_png(summary: Dict[str, Any], out_path: Path, width=800, height=600):
    img = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
        font_b = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
        font_b = font
    y = 20
    d.text((20, y), "Tabela Nutricional (estimada)", font=font_b, fill="black"); y += 40
    for k in ["total_kcal", "protein_g", "fat_g", "carbs_g", "sodium_mg"]:
        d.text((30, y), f"{k}: {summary.get(k, 0):.2f}", font=font, fill="black"); y += 28
    y += 10
    d.text((20, y), "Itens:", font=font_b, fill="black"); y += 34
    for item in summary.get("items", [])[:12]:
        line = f"- {item['name']} → {item['amount_g']:.1f} g  ({item.get('mapping')})"
        d.text((30, y), line, font=font, fill="black"); y += 22
        if y > height - 30: break
    img.save(out_path)

def png_to_pdf(png_path: Path, pdf_path: Path):
    img = Image.open(png_path)
    img.convert("RGB").save(pdf_path, "PDF")

from .render_anvisa import render_anvisa_png as render_anvisa_png
