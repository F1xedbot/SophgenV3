from fastapi import FastAPI
from src.initializer import init
from routers import agents

# Initialize environment and logging first
init()

# Create FastAPI app
app = FastAPI(
    title="SophGenV3 API",
    description="FastAPI service for SophGenV3",
    version="0.1.0",
)

# Include routers
app.include_router(agents.router, prefix="/agents", tags=["Agents"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "API is running"}