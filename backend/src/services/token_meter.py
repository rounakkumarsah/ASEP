"""
ASEP — Token Metering & Cost Attribution Service
================================================
Tracks LLM token consumption (prompt and completion) and calculates estimated USD
costs per user, workspace, and model provider. Supports monthly aggregation,
per-provider breakdowns, and end-of-month billing run-rate forecasting.
"""

from __future__ import annotations

import calendar
import datetime
import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.token_usage_log import TokenUsageLog
from src.db.postgres import _get_session_factory

logger = logging.getLogger(__name__)

# Standard per-token pricing table (prices per token in USD)
# Groq: LLaMA 3.3 70B (~$0.59 / 1M prompt, ~$0.79 / 1M completion)
# Gemini: Gemini 2.0 Flash (~$0.10 / 1M prompt, ~$0.40 / 1M completion)
# OpenRouter: standard routing / fallback rate (~$0.20 / 1M prompt, ~$0.20 / 1M completion)
PROVIDER_RATES: dict[str, dict[str, float]] = {
    "groq": {
        "input": 0.59 / 1_000_000.0,
        "output": 0.79 / 1_000_000.0,
    },
    "gemini": {
        "input": 0.10 / 1_000_000.0,
        "output": 0.40 / 1_000_000.0,
    },
    "openrouter": {
        "input": 0.20 / 1_000_000.0,
        "output": 0.20 / 1_000_000.0,
    },
    "default": {
        "input": 0.15 / 1_000_000.0,
        "output": 0.35 / 1_000_000.0,
    },
}


def parse_month_bounds(month_str: str | None = None) -> tuple[datetime.datetime, datetime.datetime, str, int]:
    """
    Parse a YYYY-MM month string into UTC start and end bounds, formatted month string,
    and total days in the month.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    if month_str:
        try:
            parts = month_str.strip().split("-")
            year = int(parts[0])
            month = int(parts[1])
            start_dt = datetime.datetime(year, month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        except Exception:
            year, month = now.year, now.month
            start_dt = datetime.datetime(year, month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    else:
        year, month = now.year, now.month
        start_dt = datetime.datetime(year, month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    days_in_month = calendar.monthrange(year, month)[1]
    if month == 12:
        end_dt = datetime.datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    else:
        end_dt = datetime.datetime(year, month + 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

    formatted_month = f"{year:04d}-{month:02d}"
    return start_dt, end_dt, formatted_month, days_in_month


class TokenMeter:
    """Service responsible for recording token usage and calculating costs."""

    @staticmethod
    def estimate_cost(provider: str, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate USD cost for a given provider and token consumption.

        Args:
            provider: Model provider name ('groq', 'gemini', 'openrouter', etc.)
            input_tokens: Number of prompt / input tokens.
            output_tokens: Number of completion / output tokens.

        Returns:
            Estimated USD cost rounded to 6 decimal places.
        """
        prov_key = (provider or "").strip().lower()
        rates = PROVIDER_RATES.get(prov_key, PROVIDER_RATES["default"])
        cost = (max(0, input_tokens) * rates["input"]) + (max(0, output_tokens) * rates["output"])
        return round(cost, 6)

    @classmethod
    async def log_usage(
        cls,
        user_id: uuid.UUID | str,
        workspace_id: str,
        provider: str,
        tokens_input: int,
        tokens_output: int,
        cost_usd: float | None = None,
        session: AsyncSession | None = None,
    ) -> TokenUsageLog:
        """
        Persist a granular token usage record to token_usage_logs.

        Args:
            user_id: User identifier.
            workspace_id: Workspace partition identifier.
            provider: Model provider (e.g. 'groq', 'gemini', 'openrouter').
            tokens_input: Prompt token count.
            tokens_output: Completion token count.
            cost_usd: Optional pre-calculated cost; if None, estimated automatically.
            session: Optional existing database session.

        Returns:
            The created TokenUsageLog record.
        """
        parsed_uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        prov_clean = (provider or "unknown").strip().lower()
        in_tokens = max(0, int(tokens_input))
        out_tokens = max(0, int(tokens_output))

        if cost_usd is None:
            calculated_cost = cls.estimate_cost(prov_clean, in_tokens, out_tokens)
        else:
            calculated_cost = round(float(cost_usd), 6)

        entry = TokenUsageLog(
            user_id=parsed_uid,
            workspace_id=str(workspace_id or "default"),
            provider=prov_clean,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            cost_usd=calculated_cost,
        )

        if session is not None:
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry

        session_factory = _get_session_factory()
        async with session_factory() as db_session:
            db_session.add(entry)
            await db_session.commit()
            await db_session.refresh(entry)
            return entry

    @classmethod
    async def get_monthly_usage(
        cls,
        user_id: uuid.UUID | str,
        month: str | None = None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Aggregate token consumption and total USD cost for a user in a given month.

        Args:
            user_id: User identifier.
            month: Optional 'YYYY-MM' string. Defaults to current UTC month.
            session: Optional existing database session.

        Returns:
            dict containing:
                - groq_tokens: total tokens consumed via Groq
                - gemini_tokens: total tokens consumed via Gemini
                - openrouter_tokens: total tokens consumed via OpenRouter
                - total_cost: total USD cost incurred
                - total_tokens: sum of all tokens across providers
                - input_tokens: total input tokens
                - output_tokens: total output tokens
                - month: formatted month string 'YYYY-MM'
                - user_id: string representation of user UUID
        """
        parsed_uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        start_dt, end_dt, formatted_month, _ = parse_month_bounds(month)

        async def _query(db_sess: AsyncSession) -> dict[str, Any]:
            stmt = select(
                TokenUsageLog.provider,
                func.coalesce(func.sum(TokenUsageLog.input_tokens), 0).label("in_sum"),
                func.coalesce(func.sum(TokenUsageLog.output_tokens), 0).label("out_sum"),
                func.coalesce(func.sum(TokenUsageLog.cost_usd), 0.0).label("cost_sum"),
            ).where(
                TokenUsageLog.user_id == parsed_uid,
                TokenUsageLog.timestamp >= start_dt,
                TokenUsageLog.timestamp < end_dt,
            ).group_by(TokenUsageLog.provider)

            res = await db_sess.execute(stmt)
            rows = res.all()

            groq_tokens = 0
            gemini_tokens = 0
            openrouter_tokens = 0
            total_cost = 0.0
            total_input = 0
            total_output = 0
            breakdown: dict[str, dict[str, Any]] = {}

            for row in rows:
                p_name = (row.provider or "unknown").lower()
                in_count = int(row.in_sum)
                out_count = int(row.out_sum)
                tot = in_count + out_count
                cost = float(row.cost_sum)

                total_input += in_count
                total_output += out_count
                total_cost += cost

                breakdown[p_name] = {
                    "input_tokens": in_count,
                    "output_tokens": out_count,
                    "total_tokens": tot,
                    "cost_usd": round(cost, 6),
                }

                if "groq" in p_name:
                    groq_tokens += tot
                elif "gemini" in p_name:
                    gemini_tokens += tot
                elif "openrouter" in p_name:
                    openrouter_tokens += tot

            return {
                "groq_tokens": groq_tokens,
                "gemini_tokens": gemini_tokens,
                "openrouter_tokens": openrouter_tokens,
                "total_cost": round(total_cost, 6),
                "total_tokens": total_input + total_output,
                "input_tokens": total_input,
                "output_tokens": total_output,
                "month": formatted_month,
                "user_id": str(parsed_uid),
                "breakdown": breakdown,
            }

        if session is not None:
            return await _query(session)

        session_factory = _get_session_factory()
        async with session_factory() as db_session:
            return await _query(db_session)

    @classmethod
    async def get_monthly_forecast(
        cls,
        user_id: uuid.UUID | str,
        month: str | None = None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Calculate projected month-end cost based on current daily run rate.

        Args:
            user_id: User identifier.
            month: Optional 'YYYY-MM' string. Defaults to current month.
            session: Optional existing database session.

        Returns:
            dict containing:
                - month: formatted month string 'YYYY-MM'
                - current_cost: cost accumulated so far in the month
                - projected_cost: linear extrapolation to end of month
                - days_elapsed: number of days elapsed into month
                - days_in_month: total days in the month
                - run_rate_per_day: average USD spend per day
                - confidence: confidence rating ('high', 'medium', 'low')
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        start_dt, end_dt, formatted_month, days_in_month = parse_month_bounds(month)

        usage = await cls.get_monthly_usage(user_id=user_id, month=formatted_month, session=session)
        current_cost = float(usage.get("total_cost", 0.0))

        # Determine days elapsed
        if now < start_dt:
            days_elapsed = 0.0
        elif now >= end_dt:
            days_elapsed = float(days_in_month)
        else:
            # Fraction of month elapsed
            seconds_elapsed = (now - start_dt).total_seconds()
            days_elapsed = max(1.0, seconds_elapsed / 86400.0)

        if days_elapsed > 0:
            daily_run_rate = current_cost / days_elapsed
        else:
            daily_run_rate = 0.0

        projected_cost = round(daily_run_rate * days_in_month, 6)

        if days_elapsed >= 7.0:
            confidence = "high"
        elif days_elapsed >= 2.0:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "month": formatted_month,
            "current_cost": round(current_cost, 6),
            "projected_cost": projected_cost,
            "days_elapsed": round(days_elapsed, 2),
            "days_in_month": days_in_month,
            "run_rate_per_day": round(daily_run_rate, 6),
            "confidence": confidence,
            "user_id": str(user_id),
        }
