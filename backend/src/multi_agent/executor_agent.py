from __future__ import annotations
from typing import Dict, Any, Optional
from src.multi_agent.contracts import AgentRole, AgentManifest, AgentRequest
from src.multi_agent.base_agent import BaseAgent
from src.ai_runtime.service import AIRuntimeService
from src.ai_runtime.contracts import CompletionRequest, Message

class ExecutionAgent(BaseAgent):
    """Execution Agent invoking AIRuntimeService, running prompts, and capturing usage telemetry."""

    def __init__(self, service: Optional[AIRuntimeService] = None) -> None:
        manifest = AgentManifest(
            name="ExecutionAgent",
            version="1.0.0",
            description="Executes generative tasks by calling AIRuntimeService.",
            capabilities=["prompt_execution", "response_normalization"],
            supported_inputs=["prompt"],
            supported_outputs=["result", "tokens_used", "provider"]
        )
        super().__init__(role=AgentRole.EXECUTOR, manifest=manifest)
        self.service = service or AIRuntimeService()

    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        prompt = request.input_data.get("prompt", "")
        
        # Prepare runtime request matching CompletionRequest contracts
        runtime_req = CompletionRequest(
            messages=[Message(role="user", content=prompt)],
            model="llama3.2",
            max_tokens=256,
            temperature=0.7
        )
        
        # Run AI completions
        resp = await self.service.complete(runtime_req)
        
        return {
            "result": resp.text,
            "tokens_used": resp.usage.total_tokens,
            "provider": resp.provider
        }
