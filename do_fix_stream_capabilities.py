import os

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

# I need to do a manual replacement in the stream function to add the exact same logic.
# Wait, the stream function is exactly the same up to the payload construction.
text = text.replace(
'''        # Pass tools if any exist
        if getattr(request, "tools", None):
            payload["tools"] = request.tools''',
'''        # Capability validation for tools
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
