import httpx
import asyncio
import json
import sys

async def test():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post('http://127.0.0.1:8000/api/v1/conversations/run', json={'thread_id': 'test-124', 'goal': 'AI agent that summarizes emails', 'research_mode': 'balanced'}, headers={'Authorization': 'Bearer test'}, timeout=30.0)
            async for line in resp.aiter_lines():
                if line:
                    print(line)
    except Exception as e:
        print(e)
asyncio.run(test())
