"""
ASEP — Billing & Token Metering Router
======================================
Provides usage aggregation and cost attribution dashboard endpoints for LLM tokens,
including monthly breakdowns per provider and run-rate cost forecasting.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Query, Request, status
from pydantic import BaseModel, Field

from src.auth.jwt import decode_token
from src.services.token_meter import TokenMeter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


class MonthlyUsageResponse(BaseModel):
    """Monthly token consumption and USD spend breakdown."""

    groq_tokens: int = Field(..., description="Total Groq tokens consumed")
    gemini_tokens: int = Field(..., description="Total Gemini tokens consumed")
    openrouter_tokens: int = Field(..., description="Total OpenRouter tokens consumed")
    total_cost: float = Field(..., description="Total estimated USD cost for the month")
    total_tokens: int = Field(..., description="Sum of all tokens across all providers")
    input_tokens: int = Field(..., description="Total prompt tokens")
    output_tokens: int = Field(..., description="Total completion tokens")
    month: str = Field(..., description="Month in YYYY-MM format")
    user_id: str = Field(..., description="User ID for which usage is aggregated")
    breakdown: dict[str, Any] = Field(default_factory=dict, description="Detailed per-provider metrics")


class ForecastResponse(BaseModel):
    """End-of-month projected cost based on current daily run rate."""

    month: str = Field(..., description="Forecasted month in YYYY-MM format")
    current_cost: float = Field(..., description="USD cost incurred so far in the month")
    projected_cost: float = Field(..., description="Estimated total cost at month end")
    days_elapsed: float = Field(..., description="Days elapsed in the month")
    days_in_month: int = Field(..., description="Total days in the month")
    run_rate_per_day: float = Field(..., description="Average USD cost per day")
    confidence: str = Field(..., description="Forecast confidence level: high, medium, low")
    user_id: str = Field(..., description="User ID for the forecast")


def _resolve_user_id(request: Request, user_id_param: uuid.UUID | None = None) -> uuid.UUID:
    """Extract authenticated user ID from parameter, Bearer token, or fallback."""
    if user_id_param:
        return user_id_param

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        try:
            payload = decode_token(token)
            if payload:
                user_id_str = payload.get("sub") or payload.get("user_id")
                if user_id_str:
                    return uuid.UUID(str(user_id_str))
        except Exception:
            pass

    if hasattr(request.state, "user_id") and request.state.user_id:
        return uuid.UUID(str(request.state.user_id))

    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.get(
    "/usage",
    response_model=MonthlyUsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Monthly Token Usage",
    description="Returns token consumption per provider (Groq, Gemini, OpenRouter) and total USD cost for a given month.",
)
async def get_usage(
    request: Request,
    month: str | None = Query(default=None, description="Target month in YYYY-MM format (e.g. 2026-09)"),
    user_id: uuid.UUID | None = Query(default=None, description="Optional user ID override"),
) -> dict[str, Any]:
    resolved_uid = _resolve_user_id(request, user_id)
    return await TokenMeter.get_monthly_usage(user_id=resolved_uid, month=month)


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Monthly Cost Forecast",
    description="Extrapolates month-end LLM costs based on current daily consumption run rate.",
)
async def get_forecast(
    request: Request,
    month: str | None = Query(default=None, description="Target month in YYYY-MM format (e.g. 2026-09)"),
    user_id: uuid.UUID | None = Query(default=None, description="Optional user ID override"),
) -> dict[str, Any]:
    resolved_uid = _resolve_user_id(request, user_id)
    return await TokenMeter.get_monthly_forecast(user_id=resolved_uid, month=month)
