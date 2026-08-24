
from fastapi import APIRouter

from src.ai_runtime.contracts import ProviderCapabilityMatrix, ProviderHealth
from src.ai_runtime.service import AIRuntimeService

router = APIRouter()
runtime_service = AIRuntimeService()

@router.get("/ai/health", response_model=list[ProviderHealth])
async def get_ai_health():
    """Query liveness, circuit breaker status, model availability, and latency across providers."""
    return await runtime_service.check_health()

@router.get("/ai/capabilities", response_model=dict[str, ProviderCapabilityMatrix])
async def get_ai_capabilities():
    """Return support capability matrices for vision, structured outputs, JSON mode, and context windows."""
    capabilities = {}
    for name, provider in runtime_service.registry.providers.items():
        capabilities[name] = provider.get_capability_matrix()
    return capabilities
