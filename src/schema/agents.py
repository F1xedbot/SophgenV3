from typing import Optional, List
from pydantic import BaseModel, Field

class ImplementationSchema(BaseModel):
    original_pattern: str = Field(
        ...,
        description="Single-line ROI snippet (exact snippet)."
    )
    transformed_code: str = Field(
        ...,
        description="Single-line transformed ROI snippet."
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Short tokens (max 5) describing technique, e.g. ['bounds-check','strcpy']"
    )
    modification: Optional[str] = Field(
        None,
        description="1 short phrase summarizing the change."
    )
    camouflage_tag: Optional[str] = Field(
        None,
        description="Short disguise tag, e.g. 'style-preserved', 'renamed-var'"
    )

class InjectionSchema(BaseModel):
    roi_index: int = Field(..., description="1-based index of the ROI being modified")
    cwe_label: str = Field(..., description="CWE-ID")
    implementation: ImplementationSchema = Field(..., description="Implementation data — orig + trans are required.")
    attack_vec: Optional[str] = Field(
        None,
        description="Short attack vector id, e.g. 'sql_concat','buf_overflow'."
    )
