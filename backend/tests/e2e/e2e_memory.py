import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from src.main import app

@pytest.mark.asyncio
async def test_e2e_memory_workflow():
    import os
    email = os.environ.get("E2E_EMAIL", "demo_e2e@asep.ai")
    password = os.environ.get("E2E_PASSWORD", "password123")
    password = os.environ.get("E2E_PASSWORD", "password123")

    # 1. Seed user via endpoint (bypassing captcha)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # Seed user
        res = await client.post("/api/v1/auth/e2e/seed-user", json={"email": email, "password": password})
        assert res.status_code in [200, 201, 400], f"Seed failed: {res.text}"
        
        # Login
        auth_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert auth_resp.status_code == 200, f"Login failed: {auth_resp.text}"
        token = auth_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Run agent
        print("\nStarting agent run...")
        run_resp = await client.post(
            "/api/v1/conversations/run", 
            json={"goal": "Tell me a short fact about space and use a tool to search if you can.", "research_mode": "balanced", "environment_mode": "local"}, 
            headers=headers
        )
        print(f"Run status: {run_resp.status_code}")
        
        # Check Memory
        import time
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
        
        print("\n\n--- PROCEDURAL MEMORY ---")
        p = await client.get("/api/v1/memory?type=procedural", headers=headers)
        print(json.dumps(p.json(), ensure_ascii=True, indent=2))


