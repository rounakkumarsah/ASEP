import os

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        res = await self.complete(request)
        yield StreamChunk(text=res.text, usage=res.usage, finish_reason=res.finish_reason)''',
'''    async def stream(self, request: CompletionRequest) -> AsyncGenerator[StreamChunk, None]:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        headers = {"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "https://asep-ai.vercel.app", "X-Title": "ASEP AI"}
        payload = {
            "model": "deepseek/deepseek-r1" if request.model == "deepseek-r1" else request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": True
        }
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        
        # Pass tools if any exist
        if getattr(request, "tools", None):
            payload["tools"] = request.tools

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            async with client.stream("POST", "/chat/completions", headers=headers, json=payload) as response:
                response.raise_for_status()
                import json
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        data_str = line[len("data: "):]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            chunk = data.get("choices", [{}])[0]
                            text = chunk.get("delta", {}).get("content", "")
                            finish_reason = chunk.get("finish_reason")
                            yield StreamChunk(text=text, usage=None, finish_reason=finish_reason)
                        except Exception:
                            pass'''
)

text = text.replace(
'''            "response_format": {"type": "json_object"}''',
'''            "response_format": {"type": "json_schema", "json_schema": {"name": "response", "schema": schema, "strict": True}}'''
)

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'w', encoding='utf-8') as f:
    f.write(text)
