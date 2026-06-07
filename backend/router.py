from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from .codebert_analyzer import CodeBERTAnalyzer
from .groq_reviewer import GroqReviewer

router = APIRouter()

codebert = CodeBERTAnalyzer()
groq     = GroqReviewer()


# ── Request schema ────────────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    code: str
    language: str = "auto"

    @field_validator("code")
    @classmethod
    def code_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("code must not be empty")
        return v


# ── Response schemas ──────────────────────────────────────────────────────────

class BugItem(BaseModel):
    line: Any = "?"        
    description: str

class FixItem(BaseModel):
    original: str
    suggested: str

class ReviewResponse(BaseModel):
    language: str
    bugs: list[BugItem]
    security_issues: list[str]
    improvements: list[str]
    fixes: list[FixItem] = []
   
    performance_scores: dict = {}
    severity: str
    summary: str


# ── Route handlers ────────────────────────────────────────────────────────────

@router.post("/review", response_model=ReviewResponse)
async def review_code(request: ReviewRequest):
    try:
        analysis = codebert.analyze(
            code=request.code,
            declared_language=request.language,
        )
        review = groq.review(
            code=request.code,
            language=analysis["language"],
            features=analysis["features"],
        )
        return ReviewResponse(
            language=analysis["language"],
            **review,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/languages")
async def supported_languages():
    return {"languages": codebert.supported_languages()}
