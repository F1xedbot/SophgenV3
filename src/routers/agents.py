from fastapi import HTTPException, APIRouter

from utils.enum import LLMModels
from services.llm import LLMService
from agents.injector import Injector
from agents.tools import InjectorTools
from services.local.cache import load_local_cache
from utils.filter import filter_dict_fields
from schema.agents import Context
from agents.states import InjectorState
from schema.requests import InjectorRequest

router = APIRouter()

@router.post("/injector", response_model=dict)
async def run_injector(req: InjectorRequest):
    llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
    loaded_cwe_cache = await load_local_cache()
    cwe_fields = ["cwe_id", "cwe_name", "vulnerable_code_patterns", "code_injection_points"]
    cwe_details = filter_dict_fields(req.cwe_ids.split(','), loaded_cwe_cache, cwe_fields)

    injector_tools = InjectorTools()
    injector_agent = Injector(llm, injector_tools)

    initial_state = InjectorState(
        messages=[],
        context=Context(
            func_code=req.func_code,
            rois=req.rois,
            cwe_details=cwe_details
        )
    )
    try:
        response = await injector_agent.run(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return response.model_dump()