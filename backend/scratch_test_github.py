import asyncio
from src.tools.github_repo import GithubRepoTool

async def main():
    tool = GithubRepoTool()
    res = await tool.execute({"url": "https://github.com/tiangolo/fastapi", "action": "init"})
    print("INIT RESULT:", res.success)
    if not res.success:
        print(res.error)
    else:
        print("FILES:", len(res.result["files"]))
        print("README:", len(res.result["readme"]))
        
        # Test read_file
        res2 = await tool.execute({"url": "https://github.com/tiangolo/fastapi", "action": "read_file", "file_path": "fastapi/__init__.py"})
        print("READ_FILE RESULT:", res2.success)
        if res2.success:
            print(res2.result["content"][:200])
            
        # Test search
        res3 = await tool.execute({"url": "https://github.com/tiangolo/fastapi", "action": "search", "query": "class FastAPI"})
        print("SEARCH RESULT:", res3.success)
        if res3.success:
            print("MATCHES:", len(res3.result["matches"]))
            print(res3.result["matches"][0])

asyncio.run(main())
