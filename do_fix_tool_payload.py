import os

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace message serialization in complete
text = text.replace(
'''            "messages": [{"role": m.role, "content": m.content} for m in request.messages],''',
'''            "messages": [{"role": m.role, "content": m.content, **({"tool_calls": m.tool_calls} if m.tool_calls else {}), **({"tool_call_id": m.tool_call_id} if m.tool_call_id else {})} for m in request.messages],'''
)

# Add tools to complete payload
text = text.replace(
'''        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens''',
'''        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
            
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice
        if request.parallel_tool_calls is not None:
            payload["parallel_tool_calls"] = request.parallel_tool_calls'''
)

# Parse tool calls in complete
text = text.replace(
'''            text = data["choices"][0]["message"]["content"]
            meta = data.get("usage", {})
            prompt_tokens = meta.get("prompt_tokens", 0)
            completion_tokens = meta.get("completion_tokens", 0)''',
'''            message_data = data["choices"][0]["message"]
            text = message_data.get("content") or ""
            
            tool_calls = None
            if "tool_calls" in message_data:
                from src.ai_runtime.contracts import ToolCall
                tool_calls = []
                for tc in message_data["tool_calls"]:
                    import json
                    args = tc["function"]["arguments"]
                    if not isinstance(args, str):
                        args = json.dumps(args)
                    tool_calls.append(ToolCall(
                        id=tc["id"],
                        type="function",
                        name=tc["function"]["name"],
                        arguments=args
                    ))

            meta = data.get("usage", {})
            prompt_tokens = meta.get("prompt_tokens", 0)
            completion_tokens = meta.get("completion_tokens", 0)'''
)

text = text.replace(
'''            return CompletionResponse(
                text=text,
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason=data["choices"][0].get("finish_reason", "stop")
            )''',
'''            return CompletionResponse(
                text=text,
                usage=usage,
                provider=self.name,
                model=request.model,
                finish_reason=data["choices"][0].get("finish_reason", "stop"),
                tool_calls=tool_calls
            )'''
)


with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'w', encoding='utf-8') as f:
    f.write(text)
