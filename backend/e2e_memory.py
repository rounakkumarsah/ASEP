import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from src.main import app

@pytest.mark.asyncio
async def test_e2e_memory_workflow():
    # 1. Seed user via endpoint (bypassing captcha)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # Seed user
        res = await client.post("/api/v1/auth/e2e/seed-user", json={"email": "demo_e2e@asep.ai", "password": "password123"})
        assert res.status_code in [200, 201, 400], f"Seed failed: {res.text}"
        
        # Login
        auth_resp = await client.post("/api/v1/auth/login", json={"email": "demo_e2e@asep.ai", "password": "password123"})
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
        
        print("\n\n--- WORKING MEMORY ---")
        w = await client.get("/api/v1/memory?type=working", headers=headers)
        print(w.json())
        
        print("\n\n--- EPISODIC MEMORY ---")
        e = await client.get("/api/v1/memory?type=episodic", headers=headers)
        print(e.json())
        
        print("\n\n--- SEMANTIC MEMORY ---")
        s = await client.get("/api/v1/memory?type=semantic", headers=headers)
        print(s.json())
        
        print("\n\n--- PROCEDURAL MEMORY ---")
        p = await client.get("/api/v1/memory?type=procedural", headers=headers)
        print(p.json())


