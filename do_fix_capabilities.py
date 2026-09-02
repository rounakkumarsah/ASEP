import os

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add _model_capabilities_cache to OpenRouterProvider
text = text.replace(
'''class OpenRouterProvider(BaseAIProvider):
    def __init__(self, api_key: str | None = None) -> None:''',
'''class OpenRouterProvider(BaseAIProvider):
    _model_capabilities_cache: dict[str, dict] = {}
    
    def __init__(self, api_key: str | None = None) -> None:'''
)

# Add capability checking method
text = text.replace(
'''    def get_capability_matrix(self) -> ProviderCapabilityMatrix:
        return ProviderCapabilityMatrix(
            streaming=True,
            structured_output=True,
            json_mode=True,
            vision=True,
            tool_calling=True,
            embeddings=True,
            reasoning=True,
            context_window=16384
        )''',
'''    async def _fetch_capabilities_if_needed(self, model: str):
        if not self._model_capabilities_cache:
            try:
                headers = {"HTTP-Referer": "https://asep-ai.vercel.app", "X-Title": "ASEP AI"}
                async with httpx.AsyncClient(base_url=self.base_url, timeout=5.0) as client:
                    resp = await client.get("/models", headers=headers)
                    if resp.status_code == 200:
                        models = resp.json().get("data", [])
                        for m in models:
                            self._model_capabilities_cache[m["id"]] = m
            except Exception:
                pass

    def get_capability_matrix(self, model: str = "") -> ProviderCapabilityMatrix:
        import asyncio
        # We can't await in sync method easily unless we run event loop, but get_capability_matrix isn't async.
        # It's fine to return a default if not fetched.
        # Since the interface is synchronous, we will return True for now but we'll use async checks in complete.
        return ProviderCapabilityMatrix(
            streaming=True,
            structured_output=True,
            json_mode=True,
            vision=True,
            tool_calling=True,
            embeddings=True,
            reasoning=True,
            context_window=16384
        )'''
)

# Modify complete to check capabilities
text = text.replace(
'''        if getattr(request, "tools", None):
            payload["tools"] = request.tools''',
'''        
        # Capability validation for tools
        await self._fetch_capabilities_if_needed(request.model)
        model_data = self._model_capabilities_cache.get(request.model, {})
        supported_params = model_data.get("supported_parameters", [])
        
        # Inject Server Tools
        server_tools = [
            {"type": "openrouter:web_search"},
            {"type": "openrouter:web_fetch"},
            {"type": "openrouter:datetime"}
        ]
        
        # Check if model supports tools before adding them
        supports_tools = "tools" in supported_params if supported_params else True
        if supports_tools:
            if getattr(request, "tools", None):
                payload["tools"] = request.tools + server_tools
            else:
                payload["tools"] = server_tools
                
        if supports_tools and request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if supports_tools and request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls'''
)


with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'w', encoding='utf-8') as f:
    f.write(text)
