from typing import List, Optional
from pydantic import BaseModel, Field

class Context(BaseModel):
    func_name: Optional[str] = None
    roi: Optional[str] = None
    cwe_details: Optional[str] = None
    func_code: str

class ValidationSchema(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being validated.")
    cwe_label: str = Field(..., description="CWE-ID from the injection.")
    is_valid: bool = Field(..., description="True if validation passed, False otherwise.")
    effectiveness: int = Field(..., description="Effectiveness score from 1 to 10.", ge=1, le=10)
    plausibility: int = Field(..., description="Plausibility score from 1 to 10.", ge=1, le=10)
    limited_to_roi: bool = Field(..., description="Whether the validation is limited to the ROI.")
    exploitability: str = Field(..., description="Brief assessment of how exploitable the vulnerability is.")
    naturalness: str = Field(..., description="Brief assessment of how natural the modified code looks.")
    maintains_functionality: str = Field(...,description="Brief assessment of whether the injection breaks functionality or compilation.")

class InjectionSchema(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being modified.")
    cwe_label: str = Field(..., description="CWE-ID.")
    original_pattern: str = Field(..., description="Single-line ROI snippet (exact snippet).")
    transformed_code: str = Field(..., description="Single-line transformed ROI snippet.")
    tags: List[str] = Field(default_factory=list, description="Short tokens (max 5) describing the technique.")
    modification: str = Field("", description="One short phrase summarizing the change. Empty string if none.")
    camouflage: str = Field("", description="Short disguise justification; empty string if none.")
    attack_vec: str = Field("", description="Short attack vector description; empty string if none.")
                            
class ValidationOuput(BaseModel):
    validation_results: list[ValidationSchema]