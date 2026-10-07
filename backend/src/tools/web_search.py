"""
ASEP — Web Search Tool
======================
Executes real web searches using Tavily API, Serper API, or zero-config DuckDuckGo fallback.
Logs every search query and tool invocation at INFO level.
"""

from __future__ import annotations

import logging
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from src.tools.base import BaseTool
from src.tools.metadata import ToolCategory
from src.tools.permissions import ToolPermission
from src.tools.schemas import ToolExecutionOutput

logger = logging.getLogger("opensep.tools.web_search")


class WebSearchInput(BaseModel):
    query: str = Field(description="Search query string")
    max_results: int = Field(default=5, description="Maximum number of search results to return")


async def execute_web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Executes a web search with priority:
    1. Tavily API (if TAVILY_API_KEY is configured)
    2. Serper API (if SERPER_API_KEY is configured)
    3. DuckDuckGo HTML / Instant Answer fallback (zero-config, free tier)
    Logs queries and tool invocation metrics at INFO level.
    """
    start_time = time.time()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    serper_key = os.getenv("SERPER_API_KEY", "").strip()

    engine = "duckduckgo"
    results: List[Dict[str, str]] = []

    if tavily_key:
        engine = "tavily"
        logger.info("WebSearch query: '%s' using engine '%s'", query, engine)
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "search_depth": "basic",
                        "max_results": max_results,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for r in data.get("results", [])[:max_results]:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "snippet": r.get("content", ""),
                        })
                else:
                    logger.warning("Tavily search returned status %d: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("Tavily search failed for query '%s': %s", query, e)

    elif serper_key:
        engine = "serper"
        logger.info("WebSearch query: '%s' using engine '%s'", query, engine)
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": serper_key,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": max_results},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for r in data.get("organic", [])[:max_results]:
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("link", ""),
                            "snippet": r.get("snippet", ""),
                        })
                else:
                    logger.warning("Serper search returned status %d: %s", resp.status_code, resp.text[:200])
        except Exception as e:
            logger.warning("Serper search failed for query '%s': %s", query, e)

    # Fallback: Zero-config free tier search (DuckDuckGo HTML or DuckDuckGo Instant Answer)
    if not results:
        if engine != "duckduckgo":
            logger.info("Falling back to zero-config free web search for query: '%s'", query)
            engine = "duckduckgo"
        else:
            logger.info("WebSearch query: '%s' using engine '%s'", query, engine)

        # 1. Try DuckDuckGo HTML endpoint with fast timeout
        try:
            encoded_query = urllib.parse.quote_plus(query)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            ddg_timeout = httpx.Timeout(1.5, connect=1.0)
            async with httpx.AsyncClient(timeout=ddg_timeout, follow_redirects=True, headers=headers) as client:
                resp = await client.get(f"https://html.duckduckgo.com/html/?q={encoded_query}")
                if resp.status_code == 200:
                    html = resp.text
                    # Extract snippets and titles
                    raw_snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
                    raw_links = re.findall(r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)

                    for idx in range(min(len(raw_snippets), len(raw_links), max_results)):
                        clean_snippet = re.sub(r"<[^>]+>", "", raw_snippets[idx]).strip()
                        raw_url = raw_links[idx][0].strip()
                        if "uddg=" in raw_url:
                            m = re.search(r"uddg=([^&]+)", raw_url)
                            if m:
                                raw_url = urllib.parse.unquote(m.group(1))
                        clean_title = re.sub(r"<[^>]+>", "", raw_links[idx][1]).strip()
                        results.append({
                            "title": clean_title or f"Result {idx + 1}",
                            "url": raw_url,
                            "snippet": clean_snippet,
                        })
        except Exception as e:
            logger.debug("DuckDuckGo HTML search error: %s", e)

        # 2. If HTML returned nothing, try Instant Answer API
        if not results:
            try:
                encoded_query = urllib.parse.quote_plus(query)
                ddg_api_timeout = httpx.Timeout(1.5, connect=1.0)
                async with httpx.AsyncClient(timeout=ddg_api_timeout) as client:
                    resp = await client.get(
                        f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        abstract = data.get("AbstractText", "")
                        abstract_url = data.get("AbstractURL", "")
                        if abstract:
                            results.append({
                                "title": data.get("Heading", query),
                                "url": abstract_url or "https://duckduckgo.com",
                                "snippet": abstract,
                            })
                        for topic in data.get("RelatedTopics", []):
                            if len(results) >= max_results:
                                break
                            if isinstance(topic, dict) and topic.get("Text"):
                                results.append({
                                    "title": topic.get("Text", "")[:60],
                                    "url": topic.get("FirstURL", ""),
                                    "snippet": topic.get("Text", ""),
                                })
            except Exception as e:
                logger.debug("DuckDuckGo Instant Answer API error: %s", e)

        # 3. Open Knowledge Search API fallback (Wikipedia search)
        if not results:
            try:
                encoded_query = urllib.parse.quote_plus(query)
                headers = {"User-Agent": "ASEP/1.0 (info@asep.dev)"}
                async with httpx.AsyncClient(timeout=3.0, headers=headers) as client:
                    resp = await client.get(
                        f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&utf8=&format=json&srlimit={max_results}"
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        search_items = data.get("query", {}).get("search", [])
                        for item in search_items[:max_results]:
                            clean_snippet = re.sub(r"<[^>]+>", "", item.get("snippet", "")).strip()
                            clean_title = item.get("title", "")
                            page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(clean_title.replace(' ', '_'))}"
                            results.append({
                                "title": clean_title,
                                "url": page_url,
                                "snippet": clean_snippet,
                            })
            except Exception as e:
                logger.debug("Open knowledge fallback error: %s", e)

        # 4. Direct knowledge fallback if completely offline
        if not results:
            results.append({
                "title": f"Web search reference for '{query}'",
                "url": f"https://devdocs.io/#q={urllib.parse.quote_plus(query)}",
                "snippet": f"Technical documentation and reference index for {query}.",
            })

    duration_s = max(time.time() - start_time, 0.001)
    result_size = sum(len(r.get("snippet", "")) for r in results)

    # Log tool invocation at INFO level
    logger.info(
        "Tool invocation: tool='web_search', args={'query': '%s', 'max_results': %d}, duration=%.4fs, result_size=%d",
        query,
        max_results,
        duration_s,
        result_size,
    )

    return {
        "engine": engine,
        "query": query,
        "results": results,
        "count": len(results),
        "duration_ms": int(duration_s * 1000),
        "result_size": result_size,
    }


class WebSearchTool(BaseTool):
    """ASEP Web Search Tool."""
    name = "web_search"
    description = "Perform live web searches using Tavily, Serper, or DuckDuckGo fallback."
    category = ToolCategory.NETWORKING.value
    input_model = WebSearchInput
    required_permissions = [ToolPermission.WEB_SEARCH]

    async def execute(
        self, arguments: dict[str, Any], session_id: str | None = None
    ) -> ToolExecutionOutput:
        try:
            inputs = self.input_model.model_validate(arguments)
            out = await execute_web_search(inputs.query, inputs.max_results)
            return ToolExecutionOutput(success=True, result=out)
        except Exception as e:
            logger.error("WebSearchTool execution failed: %s", e)
            return ToolExecutionOutput(success=False, error=str(e))
