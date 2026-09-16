import re
from typing import List, Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self):
        self.models = {
            "gemini-1.5-flash": {
                "id": "gemini-1.5-flash",
                "tier": "cheap",
                "cost_in": 0.075,
                "cost_out": 0.30,
                "latency": 0.8,
                "context": 1048576,
            },
            "llama3-8b": {
                "id": "llama3-8b",
                "tier": "cheap",
                "cost_in": 0.05,
                "cost_out": 0.05,
                "latency": 0.5,
                "context": 8192,
            },
            "gpt-4o-mini": {
                "id": "gpt-4o-mini",
                "tier": "balanced",
                "cost_in": 0.15,
                "cost_out": 0.60,
                "latency": 1.2,
                "context": 128000,
            },
            "claude-3-5-sonnet-20240620": {
                "id": "claude-3-5-sonnet-20240620",
                "tier": "premium",
                "cost_in": 3.0,
                "cost_out": 15.0,
                "latency": 2.5,
                "context": 200000,
            },
            "gpt-4o": {
                "id": "gpt-4o",
                "tier": "premium",
                "cost_in": 5.0,
                "cost_out": 15.0,
                "latency": 2.2,
                "context": 128000,
            },
        }

        # Model rate limit states
        self.degraded_models = {} # model_id -> expiry_timestamp
        self.failure_counts = {}  # model_id -> consecutive_failures
        self.routing_logs = []

    def score_task(self, prompt: str, has_tools: bool, research_mode: str) -> dict:
        """Estimate complexity from prompt length, code keywords, tools, mode."""
        score = 0
        
        # 1. Prompt length
        tok_estimate = len(prompt) // 4
        if tok_estimate > 2000:
            score += 3
        elif tok_estimate > 500:
            score += 1
            
        # 2. Code keywords
        code_keywords = ["class ", "def ", "function", "import ", "extends ", "implements ", "architecture", "kubernetes", "docker"]
        if any(kw in prompt.lower() for kw in code_keywords):
            score += 2
            
        # 3. Tool usage
        if has_tools:
            score += 2
            
        # 4. Research mode
        if research_mode == "deep":
            score += 4
        elif research_mode == "balanced":
            score += 1
            
        tier = "cheap"
        if score >= 6:
            tier = "premium"
        elif score >= 3:
            tier = "balanced"
            
        return {
            "score": score,
            "tier": tier,
            "tokens": tok_estimate
        }

    def route(self, prompt: str, has_tools: bool, research_mode: str) -> dict:
        task_info = self.score_task(prompt, has_tools, research_mode)
        tier = task_info["tier"]
        tokens = task_info["tokens"]
        
        # Clean up degraded models
        now = time.time()
        self.degraded_models = {k: v for k, v in self.degraded_models.items() if v > now}
        
        # Filter available models
        available = [m for m in self.models.values() if m["id"] not in self.degraded_models]
        if not available:
            # If all degraded, just pick the best premium
            available = list(self.models.values())
            
        # 1. Filter by context window
        capable = [m for m in available if m["context"] >= tokens + 1000]
        if not capable:
            capable = available # fallback
            
        # 2. Filter by tier
        tier_order = {"cheap": 1, "balanced": 2, "premium": 3}
        target_val = tier_order[tier]
        
        tier_models = [m for m in capable if tier_order[m["tier"]] >= target_val]
        if not tier_models:
            tier_models = capable
            
        # 3. Pick cheapest in the matched tiers
        tier_models.sort(key=lambda x: x["cost_in"])
        selected = tier_models[0]
        
        reason = f"chose {selected['id']}: complexity {task_info['score']} ({tier}), {tokens} tokens"
        
        try:
            from src.utils.metrics import metrics_store
            metrics_store.record_auto_router_decision(selected['id'])
        except Exception:
            pass
            
        return {
            "model": selected["id"],
            "reason": reason,
            "task_info": task_info
        }

    def record_failure(self, model_id: str, is_429: bool = True):
        if not is_429:
            return False
        self.failure_counts[model_id] = self.failure_counts.get(model_id, 0) + 1
        if self.failure_counts[model_id] >= 3:
            logger.warning(f"Circuit breaker tripped for {model_id}. Degraded for 5 minutes.")
            self.degraded_models[model_id] = time.time() + 300 # 5 mins
            self.failure_counts[model_id] = 0
            return True # Tripped
        return False
        
    def record_success(self, model_id: str):
        self.failure_counts[model_id] = 0

auto_router = ModelRegistry()
