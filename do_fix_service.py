import os

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\service.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace complete method execution attempt block
text = text.replace(
'''            # Execution attempt with retries
            for attempt in range(1, 3):
                try:
                    res = await provider.complete(trimmed_request)
                    if breaker:
                        breaker.record_success()

                    logger.info(
                        "UsageCollected",
                        provider=provider.name,
                        model=request.model,
                        prompt_tokens=res.usage.prompt_tokens,
                        completion_tokens=res.usage.completion_tokens,
                        total_tokens=res.usage.total_tokens,
                        latency_ms=res.usage.latency_ms
                    )
                    return res
                except Exception as exc:
                    logger.warn(
                        "RetryAttempt",
                        provider=provider.name,
                        attempt=attempt,
                        error=str(exc)
                    )
                    last_error = exc
                    time.sleep(0.1)  # Brief backoff''',
'''            # Execution attempt with retries
            for attempt in range(1, 3):
                try:
                    # Implement agentic tool calling loop
                    current_request = trimmed_request
                    max_iterations = 10
                    iterations = 0
                    
                    while iterations < max_iterations:
                        iterations += 1
                        res = await provider.complete(current_request)
                        
                        if res.finish_reason == "tool_calls" and res.tool_calls:
                            import json
                            import inspect
                            
                            # Add assistant message with tool calls
                            from src.ai_runtime.contracts import Message
                            assistant_msg = Message(role="assistant", content=res.text or "", tool_calls=[tc.model_dump() for tc in res.tool_calls])
                            current_request.messages.append(assistant_msg)
                            
                            # Execute tools
                            for tool_call in res.tool_calls:
                                if tool_call.name.startswith("openrouter:"):
                                    # Server tool - openrouter executed this, we shouldn't execute it locally
                                    continue
                                    
                                tool_result_str = ""
                                try:
                                    args = json.loads(tool_call.arguments)
                                    if current_request.tool_callables and tool_call.name in current_request.tool_callables:
                                        func = current_request.tool_callables[tool_call.name]
                                        if inspect.iscoroutinefunction(func):
                                            tool_result = await func(**args)
                                        else:
                                            tool_result = func(**args)
                                        tool_result_str = json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result
                                    else:
                                        tool_result_str = json.dumps({"error": f"Tool '{tool_call.name}' not found locally"})
                                except Exception as e:
                                    tool_result_str = json.dumps({"error": str(e)})
                                
                                tool_msg = Message(role="tool", content=tool_result_str, tool_call_id=tool_call.id)
                                current_request.messages.append(tool_msg)
                            
                            # Loop back and call model again
                            continue
                            
                        # Success without tool calls, or completed tool loop
                        if breaker:
                            breaker.record_success()

                        logger.info(
                            "UsageCollected",
                            provider=provider.name,
                            model=request.model,
                            prompt_tokens=res.usage.prompt_tokens,
                            completion_tokens=res.usage.completion_tokens,
                            total_tokens=res.usage.total_tokens,
                            latency_ms=res.usage.latency_ms
                        )
                        return res
                except Exception as exc:
                    logger.warn(
                        "RetryAttempt",
                        provider=provider.name,
                        attempt=attempt,
                        error=str(exc)
                    )
                    last_error = exc
                    import time
                    time.sleep(0.1)  # Brief backoff'''
)

with open(r'C:\Users\sachi\ASEP\backend\src\ai_runtime\service.py', 'w', encoding='utf-8') as f:
    f.write(text)
