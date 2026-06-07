
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .router import router
from dotenv import load_dotenv
load_dotenv()   # reads .env and sets all variables into os.environ

# ── Create the FastAPI app instance ──────────────────────────────────────────
app = FastAPI(
    title="AI Code Reviewer",
    description="Paste code → get bugs, improvements, and security issues",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# ✅ FIX: Read allowed origins from environment variable instead of hardcoding.
#         Comma-separated list:  "http://localhost:8501,https://myapp.streamlit.app"
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