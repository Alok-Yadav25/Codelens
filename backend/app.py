
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import router
from dotenv import load_dotenv
load_dotenv()  

# ── Create the FastAPI app instance ──────────────────────────────────────────
app = FastAPI(
    title="AI Code Reviewer",
    description="Paste code → get bugs, improvements, and security issues",
    version="1.0.0",
)


origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in origins_env.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── Register routes ───────────────────────────────────────────────────────────
app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    """Liveness check — used by Railway and Docker health checks."""
    return {"status": "ok"}
