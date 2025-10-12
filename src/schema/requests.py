from pydantic import BaseModel

class InjectorRequest(BaseModel):
    func_code: str
    rois: str
    cwe_ids: str