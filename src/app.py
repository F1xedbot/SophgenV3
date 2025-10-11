from fastapi import FastAPI
from src.initializer import init
import uvicorn

# Initialize environment & logging
init()

app = FastAPI(
    title="SophGenV3 API",
    description="FastAPI service for SophGenV3 LLM injection tasks",
    version="0.1.0",
)

# Placeholder for routes
@app.get("/")
async def root():
    return {"message": "API is running"}
