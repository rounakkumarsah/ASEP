"""
ASEP -- Organizations Router
"""
from __future__ import annotations

import contextlib
import logging
import re
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

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


class MemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    role: str = "developer"
    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "developer"


class InviteResponse(BaseModel):
    id: str
    email: str
    role: str
    status: str = "pending"
    created_at: str


class ChangeRoleRequest(BaseModel):
    role: str


class TransferOwnershipRequest(BaseModel):
    new_owner_id: uuid.UUID


@router.get("/members", response_model=list[MemberResponse])
async def list_organization_members(
    current_user: CurrentUser,
    db: DbSession,
) -> list[MemberResponse]:
    """List all members belonging to the current user's organization."""
    if not current_user.org_id:
        return [
            MemberResponse(
                id=current_user.id,
                email=current_user.email,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                role=current_user.role or "owner",
            )
        ]

    result = await db.execute(
        select(User).where(User.org_id == current_user.org_id)
    )
    users = result.scalars().all()
    return [MemberResponse.model_validate(u) for u in users]


@router.post("/invites", response_model=InviteResponse)
async def invite_member(
    payload: InviteMemberRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> InviteResponse:
    """Invite a new member to the organization by email."""
    if not current_user.org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Create or join an organization first.")

    org_res = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    valid_roles = {"owner", "admin", "developer", "manager", "billing", "viewer"}
    role = payload.role.lower()
    if role not in valid_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")

    import datetime
    invite_id = str(uuid.uuid4())
    now_str = datetime.datetime.now(datetime.UTC).isoformat()

    from src.cache.redis import get_redis_client
    redis = get_redis_client()
    if redis:
        try:
            import json
            invite_data = json.dumps({"id": invite_id, "email": payload.email, "role": role, "created_at": now_str})
            await redis.hset(f"org_invites:{org.id}", invite_id, invite_data)
        except Exception:
            pass

    return InviteResponse(id=invite_id, email=payload.email, role=role, status="pending", created_at=now_str)


@router.get("/invites", response_model=list[InviteResponse])
async def list_pending_invites(
    current_user: CurrentUser,
    db: DbSession,
) -> list[InviteResponse]:
    """List all pending invitations for the current organization."""
    if not current_user.org_id:
        return []

    from src.cache.redis import get_redis_client
    redis = get_redis_client()
    invites: list[InviteResponse] = []
    if redis:
        try:
            import json
            raw_invites = await redis.hgetall(f"org_invites:{current_user.org_id}")
            for _, inv_json in raw_invites.items():
                parsed = json.loads(inv_json if isinstance(inv_json, str) else inv_json.decode("utf-8"))
                invites.append(InviteResponse(**parsed))
        except Exception:
            pass
    return invites


@router.delete("/invites/{invite_id}")
async def revoke_invite(
    invite_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Revoke a pending invitation."""
    if not current_user.org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organization found.")

    from src.cache.redis import get_redis_client
    redis = get_redis_client()
    if redis:
        with contextlib.suppress(Exception):
            await redis.hdel(f"org_invites:{current_user.org_id}", invite_id)
    return {"status": "success", "message": "Invitation revoked successfully."}


@router.delete("/members/{member_id}")
async def remove_organization_member(
    member_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Remove a member from the organization."""
    if not current_user.org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organization found.")

    org_res = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")

    if org.owner_id != current_user.id and current_user.id != member_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the organization owner can remove members.")

    if member_id == org.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the organization owner. Transfer ownership first.")

    target_res = await db.execute(select(User).where(User.id == member_id, User.org_id == current_user.org_id))
    target_user = target_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in this organization.")

    target_user.org_id = None
    await db.flush()
    return {"status": "success", "message": "Member removed from organization."}


@router.patch("/members/{member_id}/role")
async def update_member_role(
    member_id: uuid.UUID,
    payload: ChangeRoleRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Update role for a member in the organization."""
    if not current_user.org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organization found.")

    org_res = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_res.scalar_one_or_none()
    if not org or org.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update member roles.")

    valid_roles = {"owner", "admin", "developer", "manager", "billing", "viewer"}
    if payload.role.lower() not in valid_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}")

    target_res = await db.execute(select(User).where(User.id == member_id, User.org_id == current_user.org_id))
    target_user = target_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")

    target_user.role = payload.role.lower()
    await db.flush()
    return {"status": "success", "message": f"Role updated to {payload.role}."}


@router.post("/transfer-ownership")
async def transfer_organization_ownership(
    payload: TransferOwnershipRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    """Transfer organization ownership to another member."""
    if not current_user.org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organization found.")

    org_res = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_res.scalar_one_or_none()
    if not org or org.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the current owner can transfer ownership.")

    target_res = await db.execute(select(User).where(User.id == payload.new_owner_id, User.org_id == current_user.org_id))
    target_user = target_res.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user is not a member of this organization.")

    org.owner_id = target_user.id
    target_user.role = "owner"
    current_user.role = "admin"
    await db.flush()
    return {"status": "success", "message": f"Ownership transferred to {target_user.email}."}

