from __future__ import annotations
from typing import List, Optional
from src.ai_runtime.contracts import Message

class ConversationContextManager:
    def __init__(self, token_budget: int = 4096) -> None:
        self.token_budget = token_budget

    def estimate_tokens(self, text: str) -> int:
        """Lightweight token estimator (approx 4 characters per token)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def estimate_message_tokens(self, msg: Message) -> int:
        return self.estimate_tokens(msg.content) + 4  # Metadata overhead

    def trim_messages(self, messages: List[Message], system_prompt: Optional[str] = None) -> List[Message]:
        """
        Trim conversation history to fit within token_budget.
        The system prompt is always injected at the front and preserved.
        """
        budget = self.token_budget
        system_msg = None
        
        if system_prompt:
            system_msg = Message(role="system", content=system_prompt)
            budget -= self.estimate_message_tokens(system_msg)

        trimmed: List[Message] = []
        accumulated_tokens = 0
        
        # Traverse backward to keep the most recent messages
        for msg in reversed(messages):
            if msg.role == "system":
                # System prompts are handled explicitly or overridden
                continue
            
            msg_tokens = self.estimate_message_tokens(msg)
            if accumulated_tokens + msg_tokens > budget:
                break
                
            trimmed.insert(0, msg)
            accumulated_tokens += msg_tokens

        if system_msg:
            trimmed.insert(0, system_msg)
            
        return trimmed

    def compress_context(self, messages: List[Message]) -> List[Message]:
        """Placeholder hook for semantic context compression (e.g. summarisation)."""
        return messages
