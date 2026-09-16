"""
ASEP - GitHub Repository Tool
"""
import asyncio
import logging
import os
import re
import shutil
import tempfile
import time
from typing import Any

import httpx
from pydantic import BaseModel, Field

from src.tools.base import BaseTool
from src.tools.metadata import ToolCategory
from src.tools.permissions import ToolPermission
from src.tools.schemas import ToolExecutionOutput

logger = logging.getLogger(__name__)

# Global cache for cloned repos. 
# url -> {"path": temp_dir, "expires_at": float}
REPO_CACHE: dict[str, dict[str, Any]] = {}
CACHE_TTL = 600  # 10 minutes

def cleanup_cache():
    now = time.time()
    expired = [url for url, data in REPO_CACHE.items() if data["expires_at"] < now]
    for url in expired:
        path = REPO_CACHE[url]["path"]
        try:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
        del REPO_CACHE[url]

class GithubRepoInput(BaseModel):
    url: str = Field(description="Public GitHub repository URL (e.g. https://github.com/tiangolo/fastapi)")
    action: str = Field(description="Action to perform: 'init' (clone and get tree+README), 'list_files', 'read_file', 'search'")
    file_path: str | None = Field(default=None, description="Path of the file to read (for action='read_file')")
    query: str | None = Field(default=None, description="Regex or string to search (for action='search')")

class GithubRepoTool(BaseTool):
    name = "github"
    description = "Clone, read, and search public GitHub repositories. Use 'init' to clone and get tree+README. Then use 'read_file' or 'search'."
    category = ToolCategory.DEVELOPMENT.value
    input_model = GithubRepoInput
    required_permissions = [ToolPermission.NETWORK]
    destructive_operations = False

    async def _check_size(self, owner: str, repo: str) -> str | None:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if resp.status_code == 404:
                return "Repository not found or is private."
            if resp.status_code != 200:
                return f"GitHub API error: {resp.status_code}"
            
            data = resp.json()
            size_kb = data.get("size", 0)
            if size_kb > 200 * 1024:  # > 200MB
                return f"Repository too large ({size_kb / 1024:.1f}MB). Max allowed is 200MB."
        return None

    async def execute(self, arguments: dict[str, Any], session_id: str | None = None) -> ToolExecutionOutput:
        cleanup_cache()
        try:
            inputs = self.input_model.model_validate(arguments)
            url = inputs.url.rstrip("/")
            
            # Extract owner/repo
            match = re.search(r"github\.com/([^/]+)/([^/.]+)", url)
            if not match:
                return ToolExecutionOutput(success=False, error="Invalid GitHub URL provided.")
            owner, repo_name = match.groups()

            if inputs.action == "init":
                err = await self._check_size(owner, repo_name)
                if err:
                    return ToolExecutionOutput(success=False, error=err)
                
                # Clone
                temp_dir = tempfile.mkdtemp(prefix="asep_repo_")
                proc = await asyncio.create_subprocess_exec(
                    "git", "clone", "--depth", "1", f"{url}.git", temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return ToolExecutionOutput(success=False, error=f"Clone failed: {stderr.decode()}")
                
                REPO_CACHE[url] = {"path": temp_dir, "expires_at": time.time() + CACHE_TTL}

                # Get file tree
                t_proc = await asyncio.create_subprocess_exec(
                    "git", "ls-files",
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                t_out, _ = await t_proc.communicate()
                files = [f for f in t_out.decode().split("\n") if f]

                # Find README
                readme_content = "No README found."
                for f in files:
                    if f.lower().startswith("readme"):
                        try:
                            with open(os.path.join(temp_dir, f), "r", encoding="utf-8") as rf:
                                readme_content = rf.read()[:50000] # Cap README size to 50KB
                        except Exception:
                            pass
                        break

                return ToolExecutionOutput(success=True, result={
                    "message": f"Successfully cloned and indexed {url}",
                    "files": files,
                    "readme": readme_content,
                    "repo_name": f"{owner}/{repo_name}"
                })

            # For other actions, ensure repo is cached
            if url not in REPO_CACHE:
                return ToolExecutionOutput(success=False, error="Repository not in cache. Please run 'init' action first.")
            
            repo_path = REPO_CACHE[url]["path"]
            REPO_CACHE[url]["expires_at"] = time.time() + CACHE_TTL  # refresh TTL

            if inputs.action == "list_files":
                t_proc = await asyncio.create_subprocess_exec(
                    "git", "ls-files",
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE
                )
                t_out, _ = await t_proc.communicate()
                return ToolExecutionOutput(success=True, result={"files": [f for f in t_out.decode().split("\n") if f]})

            elif inputs.action == "read_file":
                if not inputs.file_path:
                    return ToolExecutionOutput(success=False, error="file_path is required for read_file.")
                
                full_path = os.path.abspath(os.path.join(repo_path, inputs.file_path))
                if not full_path.startswith(os.path.abspath(repo_path)):
                    return ToolExecutionOutput(success=False, error="Path traversal attempt.")
                
                if not os.path.exists(full_path):
                    return ToolExecutionOutput(success=False, error=f"File not found: {inputs.file_path}")
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if len(content) > 50000:
                            content = content[:50000] + "\n\n... [File truncated at 50KB limit] ..."
                    return ToolExecutionOutput(success=True, result={"file": inputs.file_path, "content": content})
                except UnicodeDecodeError:
                    return ToolExecutionOutput(success=False, error="Cannot read binary file.")

            elif inputs.action == "search":
                if not inputs.query:
                    return ToolExecutionOutput(success=False, error="query is required for search.")
                
                s_proc = await asyncio.create_subprocess_exec(
                    "git", "grep", "-n", "-i", inputs.query,
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                s_out, s_err = await s_proc.communicate()
                
                if s_proc.returncode != 0:
                    return ToolExecutionOutput(success=True, result={"query": inputs.query, "matches": []})
                
                results = s_out.decode().split("\n")
                if len(results) > 100:
                    results = results[:100]
                    results.append("... [Search results truncated to 100 lines] ...")
                
                return ToolExecutionOutput(success=True, result={"query": inputs.query, "matches": results})

            else:
                return ToolExecutionOutput(success=False, error=f"Unknown action: {inputs.action}")

        except Exception as e:
            logger.exception("GitHubRepoTool execution failed")
            return ToolExecutionOutput(success=False, error=str(e))
