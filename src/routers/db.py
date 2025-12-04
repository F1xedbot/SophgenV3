from fastapi import APIRouter, HTTPException
from services.sqlite import SQLiteDBService
from utils.enums import AgentTable

router = APIRouter()

@router.get("/stats")
async def get_stats():
    db = SQLiteDBService()
    try:
        return await db.get_dashboard_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/injections")
async def get_injections(limit: int = 100, offset: int = 0, func_name: str = None, ref_hash: str = None):
    db = SQLiteDBService()
    try:
        if ref_hash:
            return await db.get_data_group(AgentTable.INJECTOR, group_key="ref_hash", group_value=ref_hash, limit=limit, offset=offset)
        if func_name:
            return await db.get_data_group(AgentTable.INJECTOR, group_key="func_name", group_value=func_name, limit=limit, offset=offset)
        return await db.get_data_group(AgentTable.INJECTOR, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/injections/grouped")
async def get_grouped_injections(limit: int = 100, offset: int = 0, search: str = None):
    db = SQLiteDBService()
    try:
        return await db.get_grouped_injections(limit=limit, offset=offset, search_query=search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/injections/{id}")
async def get_injection_by_id(id: int):
    db = SQLiteDBService()
    try:
        results = await db.get_data_group(AgentTable.INJECTOR, group_key="id", group_value=id)
        if not results:
            raise HTTPException(status_code=404, detail="Injection not found")
        return results[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validations")
async def get_validations(limit: int = 100, offset: int = 0, func_name: str = None, ref_hash: str = None):
    db = SQLiteDBService()
    try:
        if ref_hash:
            return await db.get_data_group(AgentTable.VALIDATOR, group_key="ref_hash", group_value=ref_hash, limit=limit, offset=offset)
        if func_name:
            return await db.get_data_group(AgentTable.VALIDATOR, group_key="func_name", group_value=func_name, limit=limit, offset=offset)
        return await db.get_data_group(AgentTable.VALIDATOR, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validations/grouped")
async def get_grouped_validations(limit: int = 100, offset: int = 0, search: str = None):
    db = SQLiteDBService()
    try:
        return await db.get_grouped_validations(limit=limit, offset=offset, search_query=search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validations/{id}")
async def get_validation_by_id(id: int):
    db = SQLiteDBService()
    try:
        results = await db.get_data_group(AgentTable.VALIDATOR, group_key="id", group_value=id)
        if not results:
            raise HTTPException(status_code=404, detail="Validation not found")
        return results[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/researches")
async def get_researches(limit: int = 100, offset: int = 0, search: str = None):
    db = SQLiteDBService()
    try:
        return await db.get_data_group(
            AgentTable.RESEARCHER, 
            limit=limit, 
            offset=offset, 
            search_column="cwe_id", 
            search_query=search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/researches/{id}")
async def get_research_by_id(id: int):
    db = SQLiteDBService()
    try:
        results = await db.get_data_group(AgentTable.RESEARCHER, group_key="id", group_value=id)
        if not results:
            raise HTTPException(status_code=404, detail="Research not found")
        return results[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/condensed")
async def get_condensed(limit: int = 100, offset: int = 0, search: str = None):
    db = SQLiteDBService()
    try:
        return await db.get_data_group(
            AgentTable.CONDENSER, 
            limit=limit, 
            offset=offset, 
            search_column="cwe_label", 
            search_query=search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/condensed/{id}")
async def get_condensed_by_id(id: int):
    db = SQLiteDBService()
    try:
        results = await db.get_data_group(AgentTable.CONDENSER, group_key="id", group_value=id)
        if not results:
            raise HTTPException(status_code=404, detail="Condensed knowledge not found")
        return results[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.delete("/injections")
async def delete_injections(ids: list[int]):
    db = SQLiteDBService()
    try:
        deleted_count = await db.delete_data_by_ids(AgentTable.INJECTOR, ids)
        return {"deleted": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/validations")
async def delete_validations(ids: list[int]):
    db = SQLiteDBService()
    try:
        deleted_count = await db.delete_data_by_ids(AgentTable.VALIDATOR, ids)
        return {"deleted": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
