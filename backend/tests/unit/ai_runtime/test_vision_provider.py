import pytest

from src.ai_runtime.contracts import CompletionRequest, Message
from src.ai_runtime.providers.vision import VisionModelProvider
from src.ai_runtime.registry import ProviderRegistry


@pytest.mark.asyncio
async def test_vision_provider_complete():
    provider = VisionModelProvider()
    req = CompletionRequest(
        messages=[Message(role="user", content="Describe screenshot layout.")],
        model="qwen2.5-vl"
    )
    resp = await provider.complete(req)
    assert resp.provider == "vision"
    assert "mock" in resp.text.lower() or resp.text != ""
    assert resp.usage.total_tokens > 0

def test_registry_resolves_vision_model():
    registry = ProviderRegistry()
    primary = registry.resolve_provider_for_model("qwen2.5-vl")
    assert primary == "vision"
