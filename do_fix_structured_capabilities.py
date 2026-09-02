import os

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''            "stream": False,
            "response_format": {"type": "json_schema", "json_schema": {"name": "response", "schema": schema, "strict": True}}
        }''',
'''            "stream": False
        }
        
        await self._fetch_capabilities_if_needed(request.model)
        model_data = self._model_capabilities_cache.get(request.model, {})
        supported_params = model_data.get("supported_parameters", [])
        
        supports_format = "response_format" in supported_params if supported_params else True
        if supports_format:
            payload["response_format"] = {"type": "json_schema", "json_schema": {"name": "response", "schema": schema, "strict": True}}
'''
)

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'w', encoding='utf-8') as f:
    f.write(text)
