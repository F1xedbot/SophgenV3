from typing import List, Optional
from pydantic import BaseModel, Field

class Context(BaseModel):
    func_name: Optional[str] = None
    rois: Optional[str] = None
    lines: Optional[str] = None
    cwe_details: Optional[str] = None
    func_code: str

class ValidationSchema(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being validated.")
    cwe_label: str = Field(..., description="CWE-ID from the injection.")
    is_valid: bool = Field(
        ...,
        description="True if the injection correctly and plausibly introduces the specified CWE flaw. False otherwise."
    )
    effectiveness: int = Field(
        ...,
        ge=1,
        le=10,
        description="Score (1-10) rating how realistically exploitable the new vulnerability is."
    )
    plausibility: int = Field(
        ...,
        ge=1,
        le=10,
        description="Score (1-10) rating how natural the code looks. A high score means it resembles a common developer mistake."
    )
    limited_to_roi: bool = Field(
        ...,
        description="True if the code modification was contained strictly within the ROI's boundaries."
    )
    exploitability: str = Field(
        ...,
        description="The concise textual rationale that justifies the 'effectiveness' score."
    )
    naturalness: str = Field(
        ...,
        description="The concise textual rationale that justifies the 'plausibility' score."
    )
    maintains_functionality: str = Field(
        ...,
        description="Assesses if the change avoids obvious compile-time errors or crashes on benign, non-malicious inputs. A good, subtle injection should preserve this superficial functionality to hide the flaw."
    )
    feedback: str = Field(
        ...,
        description="Concise reviewer verdict and reasoning (1–2 short sentences) referencing relevant ROI lines/nodes."
    )
    suggested_improvements: str = Field(
        ...,
        description="Specific, prioritized, actionable fixes or alternative injections (minimal code edits or tests) to try."
    )

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