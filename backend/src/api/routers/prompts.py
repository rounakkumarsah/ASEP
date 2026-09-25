"""
ASEP — Prompts Router
====================
Provides endpoints for retrieving system prompts.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/prompts", tags=["Prompts"])

@router.get(
    "/system",
    summary="Get the default system prompt for the playground",
)
async def get_system_prompt() -> dict[str, str]:
    """Return the default system prompt used by the playground."""
    return {
        "prompt": "You are ASEP, an expert AI-powered software engineering assistant. "
        "You help users design, build, test, and deploy software projects. "
        "You can generate code, debug issues, run tests, perform security audits, "
        "and manage deployments across multiple programming languages and frameworks."
    }
