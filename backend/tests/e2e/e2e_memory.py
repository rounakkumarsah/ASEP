import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from src.main import app

@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_memory_workflow():
    import os
    email = os.environ.get("E2E_EMAIL", "demo_e2e@asep.ai")
    password = os.environ.get("E2E_PASSWORD", "password123")
    password = os.environ.get("E2E_PASSWORD", "password123")

    # 1. Seed user via DB directly
    import uuid as _uuid
    from src.auth.password import get_password_hash
    from src.auth.service import normalize_email
    from src.db.models.user import User
    from src.api.dependencies import get_uow_factory
    
    clean_email = normalize_email(email)
    hashed = get_password_hash(password)
    
    async with get_uow_factory()() as uow:
        existing = await uow.users.get_by_email(clean_email)
        if existing:
            existing.hashed_password = hashed
            existing.email_verified = True
            existing.is_active = True
            existing.status = "active"
            await uow.commit()
        else:
            new_user = User(
                id=_uuid.uuid4(),
                username=clean_email.split("@")[0].replace(".", "_"),
                first_name="E2E",
                last_name="Tester",
                email=clean_email,
                hashed_password=hashed,
                role="developer",
                status="active",
                email_verified=True,
                is_active=True,
                mfa_enabled=False,
                account_type="individual",
                timezone="UTC",
                locale="en",
                current_plan="free",
            )
            await uow.users.create(new_user)
            await uow.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # Login
        auth_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert auth_resp.status_code == 200, f"Login failed: {auth_resp.text}"
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Run agent
        print("\nStarting agent run...")
        os.environ["SERVERLESS"] = "1"
        
        from unittest.mock import patch
        
        class MockResponse:
            def __init__(self):
                self.text = (
                    "Summary fact:\n"
                    "[\n"
                    '  {"type": "SEMANTIC", "content": "Space is a near-perfect vacuum with extremely low particle density.", "importance": 0.95},\n'
                    '  {"type": "PROCEDURAL", "content": "To calculate orbital velocity, use v = sqrt(G*M/r) and verify with telemetry.", "importance": 0.88}\n'
                    "]"
                )
        
        async def mock_complete(*args, **kwargs):
            return MockResponse()
            
        with patch("src.ai_runtime.service.AIRuntimeService.complete", new=mock_complete):
            run_resp = await client.post(
                "/api/v1/conversations/run", 
                json={"goal": "Tell me a short fact about space and use a tool to search if you can.", "research_mode": "balanced", "environment_mode": "local"}, 
                headers=headers
            )
        print(f"Run status: {run_resp.status_code}")
        
        # Check Memory
        import asyncio
        await asyncio.sleep(2)
        
        import json
        
        print("\n\n--- WORKING MEMORY ---")
        w = await client.get("/api/v1/memory?type=working", headers=headers)
        print(json.dumps(w.json(), ensure_ascii=True, indent=2))
        assert len(w.json().get("items", [])) > 0, "Working memory is empty"
        
        print("\n\n--- EPISODIC MEMORY ---")
        e = await client.get("/api/v1/memory?type=episodic", headers=headers)
        print(json.dumps(e.json(), ensure_ascii=True, indent=2))
        assert len(e.json().get("items", [])) > 0, "Episodic memory is empty"
        
        print("\n\n--- SEMANTIC MEMORY ---")
        s = await client.get("/api/v1/memory?type=semantic", headers=headers)
        print(json.dumps(s.json(), ensure_ascii=True, indent=2))
        assert len(s.json().get("items", [])) > 0, "Semantic memory is empty"
        
        print("\n\n--- PROCEDURAL MEMORY ---")
        p = await client.get("/api/v1/memory?type=procedural", headers=headers)
        print(json.dumps(p.json(), ensure_ascii=True, indent=2))
        assert len(p.json().get("items", [])) > 0, "Procedural memory is empty"


