from pydantic import BaseModel

class InjectorRequest(BaseModel):
    raw_code: str
    roi: str
    cwe_ids: str