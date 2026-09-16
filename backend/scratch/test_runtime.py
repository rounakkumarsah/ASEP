import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from src.runtime.runtime import LangGraphRuntime

class DummyWorkingMemory:
    async def set_state(self, *args, **kwargs):
        pass

class DummyMemoryManager:
    def __init__(self):
        self.working = DummyWorkingMemory()

async def test():
    try:
        runtime = LangGraphRuntime(DummyMemoryManager())
        
        print("Testing Goal: 'AI agent that summarizes emails'")
        async for event in runtime.execute_run("run-1", "thread-1", "AI agent that summarizes emails", "balanced"):
            print(event)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
