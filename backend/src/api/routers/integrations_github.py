"""
ASEP — GitHub Integration API Router
====================================
Mounted at /api/v1/integrations/github:
  - Authentication (PAT / OAuth) with encrypted token storage
  - Repository listing & creation
  - Safe push flow to 'asep/<slug>' branches
  - Two-way sync with Diff Viewer reconciliation
  - Automated Pull Request creation
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from src.utils.github_sync import (
    GitHubAccount,
    GitHubPushResult,
    GitHubRateLimitError,
    GitHubSafetyViolation,
    GitHubSyncResult,
    clear_github_token,
    get_github_account,
    get_github_token,
    github_sync_service,
    store_github_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/github", tags=["GitHub Integration"])


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class ConnectGitHubRequest(BaseModel):
    token: str = Field(description="GitHub Personal Access Token (classic with repo scope or fine-grained with read/write repo permissions)")


class GitHubStatusResponse(BaseModel):
    connected: bool
    username: str | None = None
    avatar_url: str | None = None
    scopes: list[str] = Field(default_factory=list)
    email: str | None = None


class PushGitHubRequest(BaseModel):
    repo_name: str = Field(description="Repository name (e.g. 'my-app' or 'owner/repo')")
    create_new: bool = Field(default=False, description="Whether to create a new repo on GitHub")
    private: bool = Field(default=True, description="Whether new repo is private")
    description: str = Field(default="", description="Repository description")
    language: str = Field(default="python", description="Primary language for .gitignore")
    task_summary: str = Field(default="Application built with ASEP", description="Summary of the task for commit message")
    task_slug: str = Field(default="app", description="Slug used for branch name: asep/<slug>")
    branch_name: str | None = Field(default=None, description="Explicit target branch name (must start with asep/)")
    phase: str = Field(default="deploy", description="Active pipeline phase name")
    files: dict[str, str] = Field(default_factory=dict, description="Files to push { 'main.py': '...' }")
    auto_readme: bool = Field(default=True, description="Whether to include an auto-generated README.md")


class SyncGitHubRequest(BaseModel):
    repo_name: str = Field(description="Repository full name 'owner/repo'")
    branch: str = Field(default="asep/app", description="Target branch to sync")
    local_files: dict[str, str] = Field(default_factory=dict, description="Current local files in workspace")
    last_synced_sha: str | None = Field(default=None, description="SHA of last synced commit")


class CreatePRRequest(BaseModel):
    repo_name: str = Field(description="Repository full name 'owner/repo'")
    head_branch: str = Field(description="Branch to merge from (e.g. asep/app)")
    base_branch: str = Field(default="main", description="Branch to merge into")
    title: str = Field(default="ASEP: Autonomous Feature Implementation")
    body: str = Field(default="Generated and verified autonomously by ASEP.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _get_user_key(authorization: str | None) -> str:
    """Extract user identifier from Auth header or fallback to default session."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        if token:
            # Hash prefix as stable user session key
            import hashlib
            return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    return "default_user"


@router.post("/connect", response_model=GitHubStatusResponse, summary="Connect GitHub account with PAT or OAuth token")
async def connect_github(
    payload: ConnectGitHubRequest,
    authorization: str | None = Header(default=None),
) -> GitHubStatusResponse:
    """
    Validates token via GitHub API, checks 'repo' scope, stores encrypted token,
    and returns user account details with avatar.
    """
    raw_token = payload.token.strip()
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token cannot be empty")

    try:
        account = await github_sync_service.verify_token(raw_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except GitHubRateLimitError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc))

    # Check for repo scope: either classic 'repo' in scopes or fine-grained PAT
    has_repo_scope = any("repo" in s.lower() for s in account.scopes) or len(account.scopes) == 0
    if not has_repo_scope:
        logger.warning("[GitHub] Token for %s lacks explicit 'repo' scope: %s", account.username, account.scopes)

    user_key = _get_user_key(authorization)
    store_github_token(user_key, raw_token, account=account)

    return GitHubStatusResponse(
        connected=True,
        username=account.username,
        avatar_url=account.avatar_url,
        scopes=account.scopes,
        email=account.email,
    )


@router.get("/status", response_model=GitHubStatusResponse, summary="Check GitHub connection status")
async def get_github_status(
    authorization: str | None = Header(default=None),
) -> GitHubStatusResponse:
    """Check if GitHub is connected and return account details."""
    user_key = _get_user_key(authorization)
    token = get_github_token(user_key)
    if not token:
        return GitHubStatusResponse(connected=False)

    cached_acc = get_github_account(user_key)
    if cached_acc:
        return GitHubStatusResponse(
            connected=True,
            username=cached_acc.username,
            avatar_url=cached_acc.avatar_url,
            scopes=cached_acc.scopes,
            email=cached_acc.email,
        )

    try:
        account = await github_sync_service.verify_token(token)
        store_github_token(user_key, token, account=account)
        return GitHubStatusResponse(
            connected=True,
            username=account.username,
            avatar_url=account.avatar_url,
            scopes=account.scopes,
            email=account.email,
        )
    except Exception:
        clear_github_token(user_key)
        return GitHubStatusResponse(connected=False)


@router.post("/disconnect", summary="Disconnect GitHub account")
async def disconnect_github(
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Clear stored GitHub credentials."""
    user_key = _get_user_key(authorization)
    clear_github_token(user_key)
    return {"success": True, "message": "Disconnected GitHub account."}


@router.get("/repos", summary="List user's GitHub repositories")
async def list_github_repos(
    authorization: str | None = Header(default=None),
) -> list[dict[str, Any]]:
    """Fetch user's repositories for existing-repo picker."""
    user_key = _get_user_key(authorization)
    token = get_github_token(user_key)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub not connected")

    try:
        return await github_sync_service.list_user_repos(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch repositories: {exc}")


@router.post("/push", summary="Push artifacts to a new or existing repository")
async def push_to_github(
    payload: PushGitHubRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """
    Execute push flow:
      1. Create new repo if requested
      2. Ensure target branch 'asep/<slug>' (never main)
      3. Commit files with 'ASEP: <summary> [phase: <phase>]'
      4. Return commit SHA, repo URL, and PR link
    """
    user_key = _get_user_key(authorization)
    token = get_github_token(user_key)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub not connected. Please connect in Settings -> Integrations.")

    account = await github_sync_service.verify_token(token)
    owner = account.username

    created_repo = False
    repo_name = payload.repo_name.strip()

    if "/" in repo_name:
        parts = repo_name.split("/", 1)
        owner = parts[0]
        repo_name = parts[1]

    # Step 1: Create repo if requested
    if payload.create_new:
        try:
            repo_data = await github_sync_service.create_repo(
                token=token,
                name=repo_name,
                description=payload.description,
                private=payload.private,
                auto_readme=payload.auto_readme,
                language=payload.language,
            )
            created_repo = True
            repo_name = repo_data["name"]
            owner = repo_data["owner"]["login"]
            # Brief delay for GitHub to initialize default branch refs
            import asyncio
            await asyncio.sleep(1.0)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to create repo: {exc}")

    # Step 2: Resolve default branch SHA
    try:
        default_branch, base_sha = await github_sync_service.get_default_branch_sha(token, owner, repo_name)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to inspect repository: {exc}")

    # Step 3: Target branch 'asep/<slug>' (enforces safety rule)
    if payload.branch_name:
        target_branch = payload.branch_name.strip()
        if not target_branch.startswith("asep/"):
            target_branch = f"asep/{target_branch}"
    else:
        slug = re.sub(r"[^a-zA-Z0-9_\-\.]", "-", payload.task_slug).strip("-") or "feature"
        target_branch = f"asep/{slug}"

    try:
        await github_sync_service.ensure_branch(token, owner, repo_name, target_branch, base_sha)
    except GitHubSafetyViolation as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Branch setup failed: {exc}")

    # Step 4: Atomic Commit
    commit_msg = f"ASEP: {payload.task_summary} [phase: {payload.phase}]"
    files = payload.files or {"main.py": "# Generated by ASEP\nprint('Hello from ASEP')"}

    try:
        commit_sha = await github_sync_service.push_files_to_branch(
            token=token,
            owner=owner,
            repo=repo_name,
            branch=target_branch,
            files=files,
            commit_message=commit_msg,
        )
    except GitHubSafetyViolation as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Commit failed: {exc}")

    repo_url = f"https://github.com/{owner}/{repo_name}/tree/{target_branch}"
    pr_compare_url = f"https://github.com/{owner}/{repo_name}/compare/{default_branch}...{target_branch}?expand=1"

    return {
        "success": True,
        "repo_url": repo_url,
        "branch": target_branch,
        "commit_sha": commit_sha,
        "pr_url": pr_compare_url,
        "created_repo": created_repo,
        "owner": owner,
        "repo": repo_name,
    }


@router.post("/sync", summary="Two-way sync: inspect remote changes and generate reconciliation diff")
async def sync_from_github(
    payload: SyncGitHubRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """
    Pulls latest remote files from branch, compares with local workspace,
    and returns status ('synced' | 'behind' | 'conflict') plus diffs.
    Never overwrites silently.
    """
    user_key = _get_user_key(authorization)
    token = get_github_token(user_key)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub not connected")

    parts = payload.repo_name.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="repo_name must be 'owner/repo'")
    owner, repo = parts

    try:
        latest_sha, remote_files = await github_sync_service.fetch_branch_files(
            token=token,
            owner=owner,
            repo=repo,
            branch=payload.branch,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to fetch remote branch: {exc}")

    sync_result = github_sync_service.compute_sync_status(
        local_files=payload.local_files,
        remote_files=remote_files,
        last_synced_sha=payload.last_synced_sha,
        latest_remote_sha=latest_sha,
    )

    return {
        "status": sync_result.status,
        "branch": payload.branch,
        "latest_remote_sha": sync_result.latest_remote_sha,
        "changed_files": sync_result.changed_files,
        "diffs": sync_result.diffs,
        "reconciliation_proposals": sync_result.reconciliation_proposals,
        "remote_files": remote_files,
    }


@router.post("/pull-request", summary="Open a Pull Request from asep/<slug> to base branch")
async def create_pull_request_endpoint(
    payload: CreatePRRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Open Pull Request via GitHub REST API."""
    user_key = _get_user_key(authorization)
    token = get_github_token(user_key)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub not connected")

    parts = payload.repo_name.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="repo_name must be 'owner/repo'")
    owner, repo = parts

    try:
        pr_url = await github_sync_service.create_pull_request(
            token=token,
            owner=owner,
            repo=repo,
            head_branch=payload.head_branch,
            base_branch=payload.base_branch,
            title=payload.title,
            body=payload.body,
        )
        return {"success": True, "pr_url": pr_url}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to open PR: {exc}")
