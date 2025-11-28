from __future__ import annotations
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import Dict, Any

def _ensure_font():
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))
        return "DejaVu"
    except Exception:
        return "Helvetica"

def _pct(val, dv):
    if not dv or dv <= 0:
        return None
    return max(0.0, (val / dv) * 100.0)

DV = {
    "energy_kcal": 2000.0,
    "carbs_g": 300.0,
    "added_sugars_g": 50.0, # Novo padrão
    "protein_g": 50.0,      # Alterado na nova lei (antes era 75)
    "fat_g": 55.0,
    "sat_fat_g": 20.0,      # Alterado na nova lei (antes era 22)
    "fiber_g": 25.0,
    "sodium_mg": 2000.0,
}

def _fmt(x, unit):
    if x is None:
        return "N/D"
    if unit == "kcal":
        return f"{x:.0f} kcal"
    if unit == "mg":
        return f"{x:.0f} mg"
    return f"{x:.1f} g".replace(".", ",")

def render_anvisa_vector_pdf(summary: Dict[str, Any], out_pdf: str, porcao_label="receita inteira (estimada)"):
    c = canvas.Canvas(out_pdf, pagesize=A4)
    W, H = A4
    font = _ensure_font()
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)

    margin = 15*mm
    top = H - margin
    left = margin
    right = W - margin

    c.setLineWidth(4)
    c.rect(left-5, margin-5, right-left+10, top-(margin-5), stroke=1, fill=0)

    c.setFont(font, 16)
    y = top - 8*mm
    c.drawString(left + 2*mm, y, "INFORMAÇÃO NUTRICIONAL")
    y -= 6*mm
    c.setLineWidth(2); c.line(left, y, right, y); y -= 6*mm

    c.setFont(font, 12)
    c.drawString(left + 2*mm, y, f"Porção: {porcao_label}")
    y -= 6*mm
    c.line(left, y, right, y); y -= 6*mm

    col_item = left + 2*mm
    col_100g = left + 90*mm
    col_porc = left + 125*mm
    col_vd   = left + 165*mm

    c.setFont(font, 11)
    c.drawString(col_item, y, "Item")
    c.drawString(col_100g, y, "Por 100 g")
    c.drawString(col_porc, y, "Por porção")
    c.drawString(col_vd,   y, "%VD*")
    y -= 5*mm
    c.line(left, y, right, y); y -= 6*mm

    energy = float(summary.get("total_kcal", 0.0))
    carbs  = float(summary.get("carbs_g", 0.0))
    protein= float(summary.get("protein_g", 0.0))
    fat    = float(summary.get("fat_g", 0.0))
    sodium = float(summary.get("sodium_mg", 0.0))
    fiber    = float(summary.get("fiber_g", 0.0))
    sat_fat  = float(summary.get("saturated_fat_g", 0.0))
    trans_fat= float(summary.get("trans_fat_g", 0.0))
    sugar    = float(summary.get("sugar_g", 0.0))

    total_mass = 0.0
    for it in summary.get("items", []):
        try:
            total_mass += float(it.get("amount_g", 0.0))
        except Exception:
            pass
    total_mass = max(total_mass, 0.0)

    def per100(value):
        if total_mass <= 0 or value is None:
            return None
        return value / total_mass * 100.0
    def per_portion(value):
        return value

    rows = [
        ("Valor energético",      ("kcal", energy)),
        ("Carboidratos",          ("g", carbs)),
        ("Açúcares adicionados",  ("g", sugar)),    # Novo (Opcional: Indentar visualmente)
        ("Proteínas",             ("g", protein)),
        ("Gorduras totais",       ("g", fat)),
        ("Gorduras saturadas",    ("g", sat_fat)),  # Novo
        ("Gorduras trans",        ("g", trans_fat)),# Novo
        ("Fibra alimentar",       ("g", fiber)),    # Novo
        ("Sódio",                 ("mg", sodium)),
    ]

    c.setFont(font, 11)
    for label, (unit, total_val) in rows:
        if y < 35*mm:
            c.showPage()
            c.setFont(font, 11)
            y = top - 20*mm

        v100  = per100(total_val)
        vport = per_portion(total_val)
        vd = None
        if label == "Valor energético":
            vd = _pct(vport or 0, DV["energy_kcal"])
        elif label == "Carboidratos":
            vd = _pct(vport or 0, DV["carbs_g"])
        elif label == "Açúcares adicionados":
            vd = _pct(vport or 0, DV["added_sugars_g"])
        elif label == "Proteínas":
            vd = _pct(vport or 0, DV["protein_g"])
        elif label == "Gorduras totais":
            vd = _pct(vport or 0, DV["fat_g"])
        elif label == "Gorduras saturadas":
            vd = _pct(vport or 0, DV["sat_fat_g"])
        elif label == "Fibra alimentar":
            vd = _pct(vport or 0, DV["fiber_g"])
        elif label == "Sódio":
            vd = _pct(vport or 0, DV["sodium_mg"])
        # Gorduras Trans não possui VD

        indent = 0
        if label in ["Gorduras saturadas", "Gorduras trans", "Açúcares adicionados"]:
            indent = 4*mm # Pequeno recuo

        c.drawString(col_item + indent, y, label)
        c.drawRightString(col_100g + 25*mm, y, _fmt(v100, unit))
        c.drawRightString(col_porc + 25*mm, y, _fmt(vport, unit))
        c.drawRightString(col_vd + 15*mm, y, ("N/D" if vd is None else f"{vd:.0f}%"))
        y -= 6*mm

    y -= 2*mm
    c.line(left, y, right, y); y -= 4*mm

    c.setFont(font, 9)
    c.drawString(left, y, "* % Valores Diários de referência com base em uma dieta de 2.000 kcal (8.400 kJ).")
    y -= 4*mm
    c.drawString(left, y, "  Seus valores diários podem ser maiores ou menores dependendo de suas necessidades energéticas.")
    y -= 4*mm
    c.drawString(left, y, "  Itens marcados como N/D não foram estimados nesta versão.")
    c.showPage()
    c.save()
