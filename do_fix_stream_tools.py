import os

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
'''                            text = chunk.get("delta", {}).get("content", "")
                            finish_reason = chunk.get("finish_reason")
                            yield StreamChunk(text=text, usage=None, finish_reason=finish_reason)''',
'''                            delta = chunk.get("delta", {})
                            text = delta.get("content", "")
                            finish_reason = chunk.get("finish_reason")
                            
                            # Parse streaming tool calls
                            tool_calls = None
                            if "tool_calls" in delta:
                                from src.ai_runtime.contracts import ToolCall
                                tool_calls = []
                                for tc in delta["tool_calls"]:
                                    import json
                                    args = tc["function"]["arguments"] if "function" in tc and "arguments" in tc["function"] else ""
                                    tool_calls.append(ToolCall(
                                        id=tc.get("id", ""),
                                        type="function",
                                        name=tc.get("function", {}).get("name", ""),
                                        arguments=args
                                    ))
                                    
                            yield StreamChunk(text=text, usage=None, finish_reason=finish_reason, tool_calls=tool_calls)'''
)

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\providers\openrouter.py', 'w', encoding='utf-8') as f:
    f.write(text)
