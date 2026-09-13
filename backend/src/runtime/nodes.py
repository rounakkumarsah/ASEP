import logging
from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.types import interrupt
from src.runtime.state import AgentState

logger = logging.getLogger(__name__)

NodeFunc = Callable[[AgentState], dict[str, Any] | Awaitable[dict[str, Any]]]

class NodeRegistry:
    def __init__(self) -> None:
        self._nodes: dict[str, NodeFunc] = {}
    def register(self, name: str, func: NodeFunc) -> None:
        self._nodes[name] = func
    def get_node(self, name: str) -> NodeFunc:
        return self._nodes[name]
    def get_all(self) -> dict[str, NodeFunc]:
        return self._nodes

def start_node_default(state: AgentState) -> dict[str, Any]:
    return {"status": "started", "messages": [{"role": "system", "content": "Graph started."}]}

def supervisor_node(state: AgentState) -> dict[str, Any]:
    logger.info("Supervisor Agent deciding next step...")
    return {"status": "routing", "messages": [{"role": "system", "content": "Supervisor Agent routed to Planner."}]}

def planner_node(state: AgentState) -> dict[str, Any]:
    logger.info("Planner Agent generating plan...")
    return {"status": "planning", "messages": [{"role": "system", "content": "Planner Agent generated execution plan."}]}

def research_node(state: AgentState) -> dict[str, Any]:
    logger.info("Research Agent executing MCP tools...")
    return {"status": "researching", "messages": [{"role": "system", "content": "Research Agent executed MCP tools."}]}

def rag_node(state: AgentState) -> dict[str, Any]:
    logger.info("RAG Agent performing MAG (Memory-Augmented Generation)...")
    return {"status": "rag", "messages": [{"role": "system", "content": "RAG Agent enriched context with MAG."}]}

def coding_node(state: AgentState) -> dict[str, Any]:
    logger.info("Coding Agent / AI Agent executing...")
    return {"status": "coding", "messages": [{"role": "assistant", "content": "Coding Agent completed the requested AI task with MCP & MAG context."}]}

async def human_validation_node_default(state: AgentState) -> dict[str, Any]:
    return {"status": "validated", "messages": [{"role": "system", "content": "Validated successfully."}]}

def end_node_default(state: AgentState) -> dict[str, Any]:
    return {"status": "completed"}
