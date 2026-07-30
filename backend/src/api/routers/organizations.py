"""
ASEP -- Organizations Router
"""
from __future__ import annotations

import logging
import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.db.models.organization import Organization
from src.db.models.subscription import Subscription
from src.db.models.user import User
from src.db.postgres import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:100]


class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    is_active: bool
    subscription: SubscriptionSummary | None = None
    model_config = {"from_attributes": True}


class SubscriptionSummary(BaseModel):
    plan: str
    status: str
    current_period_end: str | None = None
    model_config = {"from_attributes": True}


OrgResponse.model_rebuild()


class UpdateOrgRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: CreateOrgRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> OrgResponse:
    """Create a new organization. The requesting user becomes the owner."""
    # If user already belongs to an org, return it or update org_id
    if current_user.org_id:
        existing_org = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
        org_obj = existing_org.scalar_one_or_none()
        if org_obj:
            return OrgResponse.model_validate(org_obj)

    slug_base = _slugify(payload.name)
    slug = slug_base
    counter = 1
    while True:
        existing = await db.execute(select(Organization).where(Organization.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{slug_base}-{counter}"
        counter += 1

    # Create organization
    org = Organization(
        id=uuid.uuid4(),
        name=payload.name,
        slug=slug,
        owner_id=current_user.id,
    )
    db.add(org)
    await db.flush()

    # Assign user to new organization
    from sqlalchemy import update
    await db.execute(
        update(User)
        .where(User.id == current_user.id)
        .values(org_id=org.id)
    )
    current_user.org_id = org.id
    await db.flush()
    await db.refresh(org)

    logger.info("Organization created", extra={"org_id": str(org.id), "slug": org.slug})
    return OrgResponse.model_validate(org)


@router.get("/me", response_model=OrgResponse)
async def get_my_organization(
    current_user: CurrentUser,
    db: DbSession,
) -> OrgResponse:
    """Get the organization the current user belongs to."""
    if not current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of any organization.",
        )
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    # Fetch active subscription
    sub_result = await db.execute(
        select(Subscription)
        .where(Subscription.org_id == org.id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    subscription = sub_result.scalar_one_or_none()

    resp = OrgResponse.model_validate(org)
    if subscription:
        resp.subscription = SubscriptionSummary(
            plan=subscription.plan,
            status=subscription.status,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        )
    return resp


@router.patch("/me", response_model=OrgResponse)
async def update_organization(
    payload: UpdateOrgRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> OrgResponse:
    """Update the current user's organization."""
    if not current_user.org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No organization found.")

    result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    if org.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update organization settings.")

    if payload.name:
        org.name = payload.name
    await db.flush()
    await db.refresh(org)
    return OrgResponse.model_validate(org)
