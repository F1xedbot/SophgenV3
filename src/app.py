from fastapi import FastAPI
from src.initializer import init
from routers import agents

# Create FastAPI app
app = FastAPI(
    title="SophGenV3 API",
    description="FastAPI service for SophGenV3",
    version="0.1.0",
)

# Async initialization
@app.on_event("startup")
async def on_startup():
    await init()

app.include_router(agents.router, prefix="/agents", tags=["Agents"])

@app.get("/")
async def root():
    return {"message": "API is running"}