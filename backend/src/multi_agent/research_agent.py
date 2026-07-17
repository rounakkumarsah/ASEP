from __future__ import annotations
from typing import Dict, Any
from src.multi_agent.contracts import AgentRole, AgentManifest, AgentRequest
from src.multi_agent.base_agent import BaseAgent

class ResearchAgent(BaseAgent):
    """Research Agent performing mock web scraping and crawling (prepares for Crawl4AI integration)."""

    def __init__(self) -> None:
        manifest = AgentManifest(
            name="ResearchAgent",
            version="1.0.0",
            description="Abstracts external queries, crawling, and mock scraping interfaces.",
            capabilities=["web_research", "scraping"],
            supported_inputs=["query"],
            supported_outputs=["research_notes", "sources"]
        )
        super().__init__(role=AgentRole.RESEARCH, manifest=manifest)

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        query = request.input_data.get("query", "")
        return {
            "research_notes": f"Scraped results for: {query}. (Mock Crawl4AI result)",
            "sources": ["https://mock-crawl.url/result-1"]
        }
