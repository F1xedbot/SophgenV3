from typing import List, Optional
from pydantic import BaseModel, Field

class Context(BaseModel):
    func_name: str
    func_code: str
    lines: str
    rois: Optional[str] = None
    cwe_details: Optional[str] = None

class ResearcherSchema(BaseModel):
    """Respond to the user with this"""
    cwe_id: str = Field(..., description="Unique CWE identifier of the vulnerability.")
    cwe_name: str = Field(..., description="Official CWE title describing the vulnerability type.")
    vulnerable_code_patterns: list[str] = Field(..., description="Characteristic code constructs that lead to the vulnerability.")
    typical_code_context: str = Field(..., description="Common implementation scenarios where the vulnerability tends to occur.")
    minimal_code_modification: str = Field(..., description="Smallest code alteration that can introduce the vulnerability.")
    code_injection_points: list[str] = Field(..., description="Critical code locations where the vulnerability can be injected.")

class ValidationSchema(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being validated.")
    cwe_label: str = Field(..., description="CWE-ID from the injection.")
    ref_hash: str = Field(..., description="Unique hash of the injection")
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
    roi_index: int = Field(..., description="1-based index of the ROI being modified")
    cwe_label: str = Field(..., description="CWE-ID")
    original_pattern: str = Field(..., description="Single-line ROI snippet (exact snippet)")
    transformed_code: str = Field(..., description="Single-line transformed ROI snippet")
    tags: List[str] = Field(default_factory=list, description="Short tokens (max 5) describing the technique")
    modification: str = Field("", description="Short phrase summarizing the change")
    camouflage: str = Field("", description="Short explaination of how the injected changes were disguised to appear natural")
    attack_vec: str = Field("", description="Short explanation of how this injected vulnerability can be exploited")
                            
class ValidatorOutput(BaseModel):
    validation_results: list[ValidationSchema]

class InjectorOutput(BaseModel):
    injection_results: list[InjectionSchema]

class CondenserSchema(BaseModel):
    cwe_label: str = Field(..., description="CWE-ID.")
    works_text: str = Field(..., description="Bulleted list or concise text of strategies that worked for this CWE")
    avoid_text: str = Field(..., description="Bulleted list or concise text of strategies that failed or should be avoided")
    examples: List[str] = Field("", description="A few representative successful injections snippet")
    reasons: List[str] = Field("", description="Short reasoning why each injections worked")