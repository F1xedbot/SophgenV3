from pydantic import BaseModel
from typing import List

class InjectorRequest(BaseModel):
    raw_code: str
    roi: str
    cwe_ids: str