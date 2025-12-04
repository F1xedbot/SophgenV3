from pydantic import BaseModel

class InjectorRequest(BaseModel):
    func_name: str
    func_code: str
    lines: str
    rois: str
    cwe_ids: str

class ValidatorRequest(BaseModel):
    func_name: str
    func_code: str
    merged_roi_lines: str

class ResearcherRequest(BaseModel):
    cwe_id: str