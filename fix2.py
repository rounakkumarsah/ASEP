import sys
with open(r'C:\Users\sachi\ASEP\backend\src\api\routers\ai_runtime.py', 'r', encoding='utf-8') as f:
    text = f.read()

replacement = \"\"\"
@router.post(\"/ai-runtime/chat/completions\")
async def chat_completions(request: CompletionRequest):
    try:
        response = await runtime_service.complete(request)
        return {
            \"content\": response.text,
            \"model\": response.model,
            \"provider\": response.provider,
            \"usage\": response.usage.model_dump()
        }
    except Exception as e:
        from fastapi import HTTPException
        import traceback
        error_msg = str(e)
        if hasattr(e, '__cause__') and e.__cause__:
            error_msg += f\" (Cause: {str(e.__cause__)})\"
        raise HTTPException(status_code=400, detail=error_msg)
\"\"\"

original = \"\"\"
@router.post(\"/ai-runtime/chat/completions\")
async def chat_completions(request: CompletionRequest):
    \"\"\"Proxy AI requests to the underlying AIRuntimeService (used by the Agent Playground).\"\"\"
    # The frontend expects an OpenAI-like response object structure, 
    # but currently client extracts: res.data?.choices?.[0]?.message?.content || res.data?.content
    # The service returns a CompletionResponse with 	ext. We will format it to match what frontend expects.
    response = await runtime_service.complete(request)
    return {
        \"content\": response.text,
        \"model\": response.model,
        \"provider\": response.provider,
        \"usage\": response.usage.model_dump()
    }
\"\"\"

text = text.replace(original.strip(), replacement.strip())

with open(r'C:\Users\sachi\ASEP\backend\src\api\routers\ai_runtime.py', 'w', encoding='utf-8') as f:
    f.write(text)
