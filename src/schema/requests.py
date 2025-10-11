from pydantic import BaseModel

class InjectorRequest(BaseModel):
    func_code: str
    roi: str
    cwe_ids: str