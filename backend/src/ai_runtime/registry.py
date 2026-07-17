from __future__ import annotations
import os
from typing import Dict, List, Optional
from src.ai_runtime.providers.base import BaseAIProvider
from src.ai_runtime.providers.mock import MockProvider
from src.ai_runtime.providers.ollama import OllamaProvider
from src.ai_runtime.providers.gemini import GeminiProvider
from src.ai_runtime.providers.openai import OpenAIProvider
from src.ai_runtime.circuit_breaker import CircuitBreaker

class ProviderRegistry:
    def __init__(self) -> None:
        self.providers: Dict[str, BaseAIProvider] = {
            "ollama": OllamaProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "mock": MockProvider()
        }
        
        self.circuit_breakers: Dict[str, CircuitBreaker] = {
            "ollama": CircuitBreaker(),
            "gemini": CircuitBreaker(),
            "openai": CircuitBreaker(),
            "mock": CircuitBreaker()
        }
        
        # Load priority from env
        priority_env = os.environ.get("AI_PROVIDER_PRIORITY", "ollama,gemini,openai,mock")
        self.priority: List[str] = [p.strip().lower() for p in priority_env.split(",") if p.strip()]

    def get_provider(self, name: str) -> Optional[BaseAIProvider]:
        return self.providers.get(name.lower())

    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        return self.circuit_breakers.get(name.lower())

    def resolve_provider_for_model(self, model: str) -> str:
        """Map model names to their default/primary provider identifier."""
        model_lower = model.lower()
        if "gemini" in model_lower:
            return "gemini"
        elif "gpt-" in model_lower:
            return "openai"
        elif "mock" in model_lower:
            return "mock"
        else:
            # Default to ollama for custom models like llama, qwen, deepseek, etc.
            return "ollama"

    def get_priority_chain(self, requested_model: str) -> List[BaseAIProvider]:
        """
        Get a list of providers ordered by fallback priority.
        The primary provider for the model is placed first.
        Unhealthy providers (with OPEN circuit breakers) are skipped.
        """
        primary_name = self.resolve_provider_for_model(requested_model)
        
        chain = []
        # Place primary provider first if healthy
        if self.circuit_breakers[primary_name].allow_request():
            chain.append(self.providers[primary_name])
            
        # Append remaining healthy providers matching prioritised list
        for name in self.priority:
            if name == primary_name:
                continue
            if name in self.providers and self.circuit_breakers[name].allow_request():
                chain.append(self.providers[name])
                
        # Always fallback to mock if everything else is broken
        if "mock" in self.providers and self.providers["mock"] not in chain:
            chain.append(self.providers["mock"])
            
        return chain
