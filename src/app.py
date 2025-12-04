from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.initializer import init
from routers import db, generation
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

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

app.include_router(db.router, prefix="/api/v1/db", tags=["Database"])
app.include_router(generation.router, prefix="/api/v1/generation", tags=["Generation"])

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(static_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_path, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("db") or full_path.startswith("generation") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return {"error": "Not Found"}
        
        # Serve index.html for all other routes (SPA)
        return FileResponse(os.path.join(static_path, "index.html"))
else:
    print(f"WARNING: Static path {static_path} does not exist. Frontend will not be served.")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server with HMR
        "http://localhost:5175",  # Vite dev server with HMR and proxy
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "ok"}