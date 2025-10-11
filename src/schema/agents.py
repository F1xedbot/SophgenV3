from typing import List
from pydantic import BaseModel, Field

class Context(BaseModel):
    func_code: str
    roi: str
    cwe_details: str

class ValidationItem(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being validated")
    cwe_label: str = Field(..., description="CWE-ID from injection")
    is_valid: bool = Field(..., description="True if validation passed, False otherwise")
    effectiveness: int = Field(..., description="Effectiveness score from 1 to 10", ge=1, le=10)
    plausibility: int = Field(..., description="Plausibility score from 1 to 10", ge=1, le=10)
    limited_to_roi: bool = Field(..., description="Whether the validation is limited to the ROI")
    exploitability: str = Field(..., description="Assessment of how exploitable the vulnerability is")
    naturalness: str = Field(..., description="Assessment of how natural the code looks")
    maintains_functionality: str = Field(..., description="Assessment of normal functionality preservation")

class InjectionSchema(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being modified")
    cwe_label: str = Field(..., description="CWE-ID")
    original_pattern: str = Field(..., description="Single-line ROI snippet (exact snippet).")
    transformed_code: str = Field(..., description="Single-line transformed ROI snippet.")
    tags: List[str] = Field(default_factory=list, description="Short tokens (max 5) describing technique.")
    modification: str = Field("", description="1 short phrase summarizing the change. Empty string if none.")
    camouflage_tag: str = Field("", description="Short disguise tag; empty string if none.")
    attack_vec: str = Field("", description="Short attack vector id; empty string if none.")

class ValidationSchema(BaseModel):
    validation_results: list[ValidationItem]