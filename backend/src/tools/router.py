"""
ASEP — Tool Routing, Dispatching and Permission Enforcement
"""

import logging
import time
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from src.tools.permissions import verify_tool_permissions
from src.tools.registry import ToolRegistry
from src.tools.schemas import ToolExecutionOutput

logger = logging.getLogger(__name__)


# Structured Error Codes
class ToolErrorCode:
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_DISABLED = "TOOL_DISABLED"
    INVALID_INPUT = "INVALID_INPUT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TOOL_TIMEOUT = "TOOL_TIMEOUT"
    TOOL_UNAVAILABLE = "TOOL_UNAVAILABLE"
    INTERNAL_TOOL_ERROR = "INTERNAL_TOOL_ERROR"


class ToolDispatcher:
    """Dispatches execution requests to registered tools after checking permissions."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        # Metrics storage by tool name
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def _init_metrics(self, tool_name: str) -> None:
        if tool_name not in self.metrics:
            self.metrics[tool_name] = {
                "execution_count": 0,
                "average_latency": 0.0,
                "timeout_rate": 0.0,
                "failure_rate": 0.0,
                "failures": 0,
                "timeouts": 0,
                "last_success": None,
                "last_failure": None
            }

    def _update_metrics(self, tool_name: str, latency: float, success: bool, is_timeout: bool = False) -> None:
        self._init_metrics(tool_name)
        m = self.metrics[tool_name]
        m["execution_count"] += 1
        count = m["execution_count"]
        # Running average
        m["average_latency"] = ((m["average_latency"] * (count - 1)) + latency) / count
        
        if not success:
            m["failures"] += 1
            m["last_failure"] = time.time()
        else:
            m["last_success"] = time.time()
            
        if is_timeout:
            m["timeouts"] += 1
            
        m["failure_rate"] = m["failures"] / count
        m["timeout_rate"] = m["timeouts"] / count

    async def execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        granted_permissions: list[str],
        timeout: Optional[float] = 30.0,
        retries: int = 0,
        session_id: Optional[str] = None
    ) -> ToolExecutionOutput:
        """Route tool execution requests and enforce safety controls."""
        self._init_metrics(tool_name)
        logger.info(f"ToolStarted: '{tool_name}' with session_id='{session_id}'")
        
        # 1. Resolve Tool
        tool = self.registry.lookup(tool_name)
        if not tool:
            logger.error(f"ToolFailed: Tool '{tool_name}' not found.")
            return ToolExecutionOutput(success=False, error=ToolErrorCode.TOOL_NOT_FOUND)

        # 2. Check if enabled
        if not self.registry.is_enabled(tool_name):
            logger.error(f"ToolFailed: Tool '{tool_name}' is disabled.")
            return ToolExecutionOutput(success=False, error=ToolErrorCode.TOOL_DISABLED)

        # 3. Enforce Permission Guard
        authorized, reason = verify_tool_permissions(tool.required_permissions, granted_permissions)
        if not authorized:
            logger.warning(f"ToolFailed: Permission denied for '{tool_name}': {reason}")
            return ToolExecutionOutput(success=False, error=ToolErrorCode.PERMISSION_DENIED)

        # 4. Input Validation
        try:
            validated_args = tool.validate(arguments)
        except ValidationError as ve:
            logger.warning(f"ToolFailed: Invalid input for '{tool_name}': {ve}")
            return ToolExecutionOutput(success=False, error=f"{ToolErrorCode.INVALID_INPUT}: {ve}")

        # 5. Check Health
        health_info = tool.health()
        if not health_info.get("available", False):
            logger.error(f"ToolFailed: Tool '{tool_name}' is unavailable. Reason: {health_info.get('error')}")
            return ToolExecutionOutput(success=False, error=ToolErrorCode.TOOL_UNAVAILABLE)

        # 6. Execute with Retries & Timeout
        attempt = 0
        while attempt <= retries:
            start_time = time.time()
            if attempt > 0:
                logger.info(f"ToolRetry: Retrying '{tool_name}' (attempt {attempt}/{retries})")
            
            try:
                # Wrap with asyncio.wait_for to handle timeout
                if timeout:
                    output = await asyncio.wait_for(tool.execute(validated_args, session_id=session_id), timeout=timeout)
                else:
                    output = await tool.execute(validated_args, session_id=session_id)
                
                latency = time.time() - start_time
                self._update_metrics(tool_name, latency, output.success)
                
                if output.success:
                    logger.info(f"ToolCompleted: '{tool_name}' executed successfully in {latency:.4f}s.")
                    return output
                else:
                    logger.warning(f"ToolFailed: '{tool_name}' returned failure: {output.error}")
                    if attempt == retries:
                        return output
            except asyncio.TimeoutError:
                latency = time.time() - start_time
                self._update_metrics(tool_name, latency, success=False, is_timeout=True)
                logger.error(f"ToolTimeout: '{tool_name}' timed out after {timeout}s.")
                if attempt == retries:
                    return ToolExecutionOutput(success=False, error=ToolErrorCode.TOOL_TIMEOUT)
            except Exception as e:
                latency = time.time() - start_time
                self._update_metrics(tool_name, latency, success=False)
                logger.error(f"ToolFailed: Internal error during '{tool_name}' execution: {e}")
                if attempt == retries:
                    return ToolExecutionOutput(success=False, error=f"{ToolErrorCode.INTERNAL_TOOL_ERROR}: {e}")
            
            attempt += 1

        return ToolExecutionOutput(success=False, error=ToolErrorCode.INTERNAL_TOOL_ERROR)


# Alias for backwards compatibility
ToolRouter = ToolDispatcher
