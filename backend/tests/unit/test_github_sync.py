"""
ASEP — GitHub Sync Engine Unit Tests
====================================
Tests verifying:
1. Token storage encryption & retrieval (Fernet PBKDF2)
2. Safety guards:
   - Rejection of pushes to protected branches (main, master)
   - Prevention of force-pushing
3. Token scope enforcement (strictly 'repo' scope)
4. Repository and branch name formatting (asep/<task-slug>)
5. Rate limit backoff and error handling
6. Git Data API atomic tree push and PR creation
7. Two-way synchronization & conflict reconciliation
8. FastAPI Integration API endpoints
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.utils.github_sync import (
    GitHubAccount,
    GitHubPushResult,
    GitHubRateLimitError,
    GitHubSafetyViolation,
    GitHubSyncResult,
    GitHubSyncService,
    clear_github_token,
    get_github_token,
    get_gitignore_template,
    github_sync_service,
    store_github_token,
)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Token Encryption & Storage Tests
# ---------------------------------------------------------------------------

class TestTokenEncryptionStorage:
    def test_store_and_retrieve_encrypted_token(self):
        user_id = "test_user_42"
        raw_token = "ghp_MockSecretTokenValue1234567890"

        store_github_token(user_id, raw_token)
        retrieved = get_github_token(user_id)

        assert retrieved == raw_token
        # Verify it is not stored as plain text in internal storage
        from src.utils.github_sync import _STORED_TOKENS
        stored_raw = _STORED_TOKENS[user_id]
        assert stored_raw != raw_token
        assert stored_raw.startswith("enc:")

        # Clear token
        clear_github_token(user_id)
        assert get_github_token(user_id) is None


# ---------------------------------------------------------------------------
# 2. Safety Invariants Tests
# ---------------------------------------------------------------------------

class TestGitHubSafetyInvariants:
    def test_protected_branch_safety_guard(self):
        service = GitHubSyncService()

        # Target branch 'main' must be rejected
        with pytest.raises(GitHubSafetyViolation, match="Cannot push directly to protected branch 'main'"):
            service.validate_branch_safety("main")

        # Target branch 'master' must be rejected
        with pytest.raises(GitHubSafetyViolation, match="Cannot push directly to protected branch 'master'"):
            service.validate_branch_safety("master")

        # Safe feature branch must pass
        service.validate_branch_safety("asep/fix-login-modal")
        service.validate_branch_safety("feature/new-api")

    def test_force_push_safety_guard(self):
        service = GitHubSyncService()

        # Force push must be forbidden
        with pytest.raises(GitHubSafetyViolation, match="Force-pushing to GitHub is strictly forbidden"):
            service.validate_force_push_safety(force=True)

        # Non-force push is allowed
        service.validate_force_push_safety(force=False)


# ---------------------------------------------------------------------------
# 3. Language .gitignore Templates
# ---------------------------------------------------------------------------

class TestGitignoreTemplates:
    def test_python_gitignore(self):
        gi = get_gitignore_template("python")
        assert "__pycache__/" in gi
        assert ".venv/" in gi

    def test_node_typescript_gitignore(self):
        gi = get_gitignore_template("typescript")
        assert "node_modules/" in gi
        assert ".next/" in gi

    def test_fallback_gitignore(self):
        gi = get_gitignore_template("custom_unknown_lang")
        assert ".env" in gi


# ---------------------------------------------------------------------------
# 4. Token Scope & Authentication Verification
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGitHubAuthAndScopes:
    async def test_verify_token_with_valid_repo_scope(self):
        service = GitHubSyncService()

        mock_user_resp = MagicMock(spec=httpx.Response)
        mock_user_resp.status_code = 200
        mock_user_resp.headers = {"x-oauth-scopes": "repo, user:email"}
        mock_user_resp.json.return_value = {
            "login": "octocat",
            "avatar_url": "https://avatars.githubusercontent.com/u/583231",
            "email": "octocat@github.com",
        }

        with patch.object(service, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_user_resp

            account = await service.verify_token("ghp_valid_token_with_repo_scope")
            assert account.username == "octocat"
            assert account.avatar_url == "https://avatars.githubusercontent.com/u/583231"
            assert "repo" in account.scopes

    async def test_verify_token_missing_repo_scope(self):
        service = GitHubSyncService()

        mock_user_resp = MagicMock(spec=httpx.Response)
        mock_user_resp.status_code = 200
        mock_user_resp.headers = {"x-oauth-scopes": "public_repo, read:user"}
        mock_user_resp.json.return_value = {"login": "unprivileged_user", "avatar_url": ""}

        with patch.object(service, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = mock_user_resp

            with pytest.raises(ValueError, match="Token lacks required 'repo' scope"):
                await service.verify_token("ghp_insufficient_token")

    async def test_rate_limit_detection(self):
        service = GitHubSyncService()

        mock_rate_limit_resp = MagicMock(spec=httpx.Response)
        mock_rate_limit_resp.status_code = 403
        mock_rate_limit_resp.headers = {
            "x-ratelimit-remaining": "0",
            "x-ratelimit-reset": "1700000000",
        }
        mock_rate_limit_resp.text = "API rate limit exceeded"

        with patch("httpx.AsyncClient.send", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = mock_rate_limit_resp

            with pytest.raises(GitHubRateLimitError, match="GitHub API rate limit exceeded"):
                await service._request("GET", "/user", "ghp_any_token")


# ---------------------------------------------------------------------------
# 5. Git Data API Atomic Push & Branch Isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestGitPushOperations:
    async def test_push_workspace_rejects_main(self):
        service = GitHubSyncService()
        with pytest.raises(GitHubSafetyViolation):
            await service.push_workspace(
                token="dummy",
                owner="testowner",
                repo="testrepo",
                branch="main",
                files={"main.py": "print('hello')"},
            )

    async def test_push_workspace_creates_blobs_and_tree(self):
        service = GitHubSyncService()

        def fake_request(method, endpoint, token, **kwargs):
            resp = MagicMock(spec=httpx.Response)
            resp.status_code = 200
            if "refs/heads" in endpoint and method == "GET":
                resp.json.return_value = {"object": {"sha": "base123sha"}}
            elif "git/blobs" in endpoint:
                resp.json.return_value = {"sha": "blob456sha"}
            elif "git/trees" in endpoint:
                resp.json.return_value = {"sha": "tree789sha"}
            elif "git/commits" in endpoint:
                resp.json.return_value = {"sha": "commitabcsha"}
            elif "refs/heads" in endpoint and method == "PATCH":
                # Verify non-force push
                assert kwargs.get("json_data", {}).get("force") is False
                resp.json.return_value = {"ref": "refs/heads/asep/test-task"}
            return resp

        with patch.object(service, "_request", new_callable=AsyncMock, side_effect=fake_request):
            commit_sha = await service.push_workspace(
                token="dummy",
                owner="testowner",
                repo="testrepo",
                branch="asep/test-task",
                files={"app/main.py": "print('hello')", "README.md": "# Test"},
                commit_message="ASEP: add auth flow [phase: implement]",
            )
            assert commit_sha == "commitabcsha"


# ---------------------------------------------------------------------------
# 6. Two-Way Sync and Non-Destructive Reconciliation
# ---------------------------------------------------------------------------

class TestSyncReconciliation:
    def test_reconcile_file_content_no_conflict(self):
        service = GitHubSyncService()
        local_code = "def hello():\n    return 'local'"
        remote_code = "def hello():\n    return 'local'\n\ndef new_from_github():\n    return True"

        reconciled = service.reconcile_file_content(local_code, remote_code)
        assert "def new_from_github():" in reconciled
        assert "return 'local'" in reconciled
        assert "<<<<<<<" not in reconciled

    def test_reconcile_file_content_with_conflict(self):
        service = GitHubSyncService()
        local_code = "app_title = 'ASEP Local'"
        remote_code = "app_title = 'ASEP Cloud'"

        reconciled = service.reconcile_file_content(local_code, remote_code)
        assert "<<<<<<< LOCAL" in reconciled
        assert "app_title = 'ASEP Local'" in reconciled
        assert "=======" in reconciled
        assert "app_title = 'ASEP Cloud'" in reconciled
        assert ">>>>>>> REMOTE" in reconciled

    def test_compute_sync_status_detection(self):
        service = GitHubSyncService()
        local_files = {"app.py": "code_v1"}
        remote_files = {"app.py": "code_v2"}

        sync_res = service.compute_sync_status(
            local_files=local_files,
            remote_files=remote_files,
            last_synced_sha="sha_old",
            latest_remote_sha="sha_new",
        )
        assert sync_res.status in ("behind", "conflict")
        assert "app.py" in sync_res.changed_files
        assert "app.py" in sync_res.diffs
        assert "app.py" in sync_res.reconciliation_proposals


# ---------------------------------------------------------------------------
# 7. Integration API Endpoints Tests
# ---------------------------------------------------------------------------

class TestGitHubAPIEndpoints:
    def test_get_status_disconnected_by_default(self, client):
        resp = client.get("/api/v1/integrations/github/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["connected"] is False

    def test_connect_with_invalid_token(self, client):
        with patch.object(github_sync_service, "verify_token", side_effect=ValueError("Invalid GitHub token")):
            resp = client.post(
                "/api/v1/integrations/github/connect",
                json={"token": "ghp_invalid_token_xyz"},
            )
            assert resp.status_code == 400
            assert "Invalid GitHub token" in resp.json()["detail"]

    def test_connect_success(self, client):
        mock_acc = GitHubAccount(
            username="dev-asep",
            avatar_url="https://github.com/dev-asep.png",
            scopes=["repo"],
            email="dev@asep.ai",
        )
        with patch.object(github_sync_service, "verify_token", new_callable=AsyncMock, return_value=mock_acc):
            resp = client.post(
                "/api/v1/integrations/github/connect",
                json={"token": "ghp_valid_secret_repo_token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["connected"] is True
            assert data["username"] == "dev-asep"
            assert "repo" in data["scopes"]

        # Now status should be connected
        status_resp = client.get("/api/v1/integrations/github/status")
        assert status_resp.status_code == 200
        assert status_resp.json()["connected"] is True

        # Disconnect
        disc_resp = client.post("/api/v1/integrations/github/disconnect")
        assert disc_resp.status_code == 200
        assert client.get("/api/v1/integrations/github/status").json()["connected"] is False

    def test_push_without_authentication_fails(self, client):
        resp = client.post(
            "/api/v1/integrations/github/push",
            json={
                "repo_name": "test-repo",
                "create_new": False,
                "task_summary": "Test push",
                "files": {"main.py": "print(1)"},
            },
        )
        assert resp.status_code == 401
        assert "GitHub not connected" in resp.json()["detail"]

    def test_push_success_flow(self, client):
        mock_acc = GitHubAccount(username="rounakkumarsah", avatar_url="", scopes=["repo"])
        store_github_token("default_user", "ghp_valid_mock_token", account=mock_acc)

        with patch.object(github_sync_service, "verify_token", new_callable=AsyncMock, return_value=mock_acc), \
             patch.object(github_sync_service, "get_default_branch_sha", new_callable=AsyncMock, return_value=("main", "commit123sha")), \
             patch.object(github_sync_service, "ensure_branch", new_callable=AsyncMock, return_value="commit123sha"), \
             patch.object(github_sync_service, "push_files_to_branch", new_callable=AsyncMock, return_value="commit123sha"), \
             patch.object(github_sync_service, "create_pull_request", new_callable=AsyncMock, return_value="https://github.com/rounakkumarsah/test/pull/1"):

            resp = client.post(
                "/api/v1/integrations/github/push",
                json={
                    "repo_name": "rounakkumarsah/test",
                    "create_new": False,
                    "task_summary": "Add authentication module",
                    "branch_name": "asep/auth-module",
                    "files": {"auth.py": "def auth(): pass"},
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["branch"] == "asep/auth-module"
            assert data["commit_sha"] == "commit123sha"
            assert "compare" in data["pr_url"] or "pull" in data["pr_url"]

        clear_github_token("default_user")

