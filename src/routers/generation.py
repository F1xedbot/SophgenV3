from fastapi import APIRouter, HTTPException
from utils.enums import LLMModels
from services.llm import LLMService
from agents.injector import Injector
from agents.validator import Validator
from agents.researcher import Researcher
from agents.states import ResearcherState
from agents.tools import CondenserTools
from schema.agents import Context
from schema.requests import InjectorRequest, ValidatorRequest, ResearcherRequest
from services.sqlite import SQLiteDBService
from utils.enums import AgentTable
import orjson
import os
import pandas as pd
import uuid

router = APIRouter()

@router.post("/injection")
async def generate_injection(req: InjectorRequest):
    if not req.func_code or not req.func_name or not req.cwe_ids:
        return False

    try:
        llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
        condenser_tools = CondenserTools()
        merged_data = await condenser_tools.enrich_cwe_details(req.cwe_ids)
        cwe_details_str = orjson.dumps(merged_data, option=orjson.OPT_INDENT_2).decode("utf-8")

        injector = Injector(llm)
        await injector.run(context=Context(
            func_name=req.func_name,
            func_code=req.func_code,
            lines=req.lines,
            rois=req.rois,
            cwe_details=cwe_details_str
        ))
        return True
    except Exception as e:
        print(f"Error in generate_injection: {e}")
        return False

@router.post("/validation")
async def generate_validation(req: ValidatorRequest):
    if not req.func_code or not req.func_name:
        return False

    try:
        llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
        validator = Validator(llm)
        context = Context(
            func_code=req.func_code,
            func_name=req.func_name,
            lines=req.merged_roi_lines
        )
        await validator.run(context)
        return True
    except Exception as e:
        print(f"Error in generate_validation: {e}")
        return False

@router.post("/research")
async def generate_research(req: ResearcherRequest):
    if not req.cwe_id:
        return False

    db = SQLiteDBService()
    try:
        # Check if research already exists
        existing = await db.get_data_group(AgentTable.RESEARCHER, "cwe_id", req.cwe_id)
        if existing:
            return True

        llm = LLMService(LLMModels.GEMINI_2_5_FLASH_LITE)
        researcher = Researcher(llm)
        
        state = ResearcherState(messages=[], cwe_id=req.cwe_id)
        await researcher.run(state)
        return True
    except Exception as e:
        print(f"Error in generate_research: {e}")
        return False

@router.get("/sample")
async def get_sample():
    csv_path = os.path.join("src", "scripts", "data", "merged_test_input.csv")
    
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Sample data file not found")
        
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
             raise HTTPException(status_code=404, detail="CSV file is empty")
        sample_row = df.sample(n=1).iloc[0]
        row = sample_row.to_dict()
        random_hash = str(uuid.uuid4())[:8]
        current_func = row.get('func_name', 'unknown')
        row['func_name'] = f"{current_func}_{random_hash}"
        return row
    except Exception as e:
        print(f"Error getting sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))
