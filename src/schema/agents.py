from typing import List
from pydantic import BaseModel, Field

class Context(BaseModel):
    raw_code: str
    roi: str
    cwe_details: str

class InjectionSchema(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being modified")
    cwe_label: str = Field(..., description="CWE-ID")
    original_pattern: str = Field(..., description="Single-line ROI snippet (exact snippet).")
    transformed_code: str = Field(..., description="Single-line transformed ROI snippet.")
    tags: List[str] = Field(default_factory=list, description="Short tokens (max 5) describing technique.")
    modification: str = Field("", description="1 short phrase summarizing the change. Empty string if none.")
    camouflage_tag: str = Field("", description="Short disguise tag; empty string if none.")
    attack_vec: str = Field("", description="Short attack vector id; empty string if none.")