from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any

class JobCreate(BaseModel):
    input_type: Literal["auto", "text", "html", "url"] = "auto"
    content: str = Field(..., description="Texto, HTML ou URL dependendo do input_type")
    extractor: Optional[Literal["regex", "llm", "auto"]] = "auto"
    label_format: Optional[Literal["simple", "anvisa"]] = "anvisa"

class JobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "done", "error"]
    message: Optional[str] = None
    created_at: float
    updated_at: float
    results: Optional[Dict[str, Any]] = None  # paths relativos quando pronto

class IngredientItem(BaseModel):
    name: str
    quantity: float
    unit: str
    note: Optional[str] = None

class NutritionItem(BaseModel):
    name: str
    amount_g: float
    mapping: Optional[str] = None
    kcal: float = 0.0
    protein_g: float = 0.0
    fat_g: float = 0.0
    carbs_g: float = 0.0
    sodium_mg: float = 0.0

class NutritionSummary(BaseModel):
    total_kcal: float
    protein_g: float
    fat_g: float
    carbs_g: float
    sodium_mg: float
    per_serving: Optional[Dict[str, float]] = None
    items: List[NutritionItem] = []
