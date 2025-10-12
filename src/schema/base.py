from pydantic import BaseModel

class FunctionRawSchema(BaseModel):
    func_name: str
    func_code: str
    data_src: str
    dot: str
    vuln: bool

class FunctionMetadataSchema(BaseModel):
    collapsed_graph: str
    func_name: str
    data_src: str
    cwe_ids: str
    rois: str