import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        req = {"code": "def fib(n):\n    return n if n <= 1 else fib(n-1) + fib(n-2)\nprint([fib(i) for i in range(10)])\n"}
        async with client.stream("POST", "http://localhost:8000/api/v1/sandbox/python/stream", json=req) as response:
            async for chunk in response.aiter_text():
                print(chunk, end="")

asyncio.run(main())
