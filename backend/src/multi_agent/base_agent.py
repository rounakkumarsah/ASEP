from __future__ import annotations
import abc
import asyncio
import time
import logging
import uuid
from typing import Any, Dict, List, Optional
from src.multi_agent.contracts import (
    AgentRole,
    AgentState,
    AgentManifest,
    AgentEventName,
    AgentEvent,
    AgentRequest,
    AgentResponse
)

logger = logging.getLogger(__name__)

class BaseAgent(abc.ABC):
    """Abstract BaseAgent implementing standardized execution, retries, timeouts, and state tracking."""

    def __init__(self, role: AgentRole, manifest: AgentManifest, max_retries: int = 3, retry_delay: float = 1.0) -> None:
        self.role = role
        self._manifest = manifest
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.state = AgentState.IDLE
        self._is_enabled = True

    def metadata(self) -> AgentManifest:
        return self._manifest

    def capabilities(self) -> List[str]:
        return self._manifest.capabilities

    def health(self) -> bool:
        """Check agent health and status."""
        return self._is_enabled

    def enable(self) -> None:
        self._is_enabled = True

    def disable(self) -> None:
        self._is_enabled = False
        self.state = AgentState.CANCELLED

    def validate_inputs(self, data: Dict[str, Any]) -> bool:
        """Verify request contains all required schema keys."""
        for field in self._manifest.supported_inputs:
            if field not in data:
                logger.warning(f"Validation failed for agent {self.role.value}: missing field '{field}'")
                return False
        return True

    def validate_outputs(self, data: Dict[str, Any]) -> bool:
        """Verify response contains all required output schema keys."""
        for field in self._manifest.supported_outputs:
            if field not in data:
                logger.warning(f"Validation failed for agent {self.role.value}: missing output field '{field}'")
                return False
        return True

    def _emit_event(
        self,
        execution_id: str,
        correlation_id: str,
        event_name: AgentEventName,
        message: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> None:
        event = AgentEvent(
            event_id=str(uuid.uuid4()),
            execution_id=execution_id,
            correlation_id=correlation_id,
            event_name=event_name,
            agent_role=self.role,
            message=message,
            timestamp=time.time(),
            payload=payload or {}
        )
        logger.info(f"AgentEvent: {event.event_name.value} - {event.message}", extra={"event": event.dict()})

    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Executes the agent logic with inputs validation, retry policies, timeouts, and state telemetry."""
        if not self._is_enabled:
            return AgentResponse(
                execution_id=request.execution_id,
                correlation_id=request.correlation_id,
                status=AgentState.FAILED,
                error_message="Agent is currently disabled."
            )

        self.state = AgentState.RUNNING
        self._emit_event(
            execution_id=request.execution_id,
            correlation_id=request.correlation_id,
            event_name=AgentEventName.AGENT_STARTED,
            message=f"Agent {self.role.value} started execution."
        )

        # Validate Inputs
        if not self.validate_inputs(request.input_data):
            self.state = AgentState.FAILED
            self._emit_event(
                execution_id=request.execution_id,
                correlation_id=request.correlation_id,
                event_name=AgentEventName.AGENT_FAILED,
                message=f"Agent {self.role.value} failed input validation."
            )
            return AgentResponse(
                execution_id=request.execution_id,
                correlation_id=request.correlation_id,
                status=AgentState.FAILED,
                error_message="Input validation failed."
            )

        attempt = 0
        last_error = None
        
        while attempt <= self.max_retries:
            if attempt > 0:
                self.state = AgentState.RETRYING
                self._emit_event(
                    execution_id=request.execution_id,
                    correlation_id=request.correlation_id,
                    event_name=AgentEventName.AGENT_RETRY,
                    message=f"Agent {self.role.value} retrying attempt {attempt}.",
                    payload={"attempt": attempt}
                )
                await asyncio.sleep(self.retry_delay * (2 ** (attempt - 1)))

            attempt += 1
            try:
                # Execute with Timeout wrapper
                output_data = await asyncio.wait_for(
                    self._execute_internal(request),
                    timeout=request.timeout_seconds
                )
                
                # Validate Outputs
                if not self.validate_outputs(output_data):
                    raise ValueError("Output validation failed.")

                self.state = AgentState.COMPLETED
                self._emit_event(
                    execution_id=request.execution_id,
                    correlation_id=request.correlation_id,
                    event_name=AgentEventName.AGENT_COMPLETED,
                    message=f"Agent {self.role.value} completed successfully."
                )
                return AgentResponse(
                    execution_id=request.execution_id,
                    correlation_id=request.correlation_id,
                    status=AgentState.COMPLETED,
                    output_data=output_data
                )

            except asyncio.TimeoutError as te:
                last_error = f"Execution timed out after {request.timeout_seconds}s"
                self._emit_event(
                    execution_id=request.execution_id,
                    correlation_id=request.correlation_id,
                    event_name=AgentEventName.AGENT_TIMEOUT,
                    message=f"Agent {self.role.value} execution timed out."
                )
            except Exception as e:
                last_error = str(e)
                logger.error(f"Error during agent {self.role.value} execute: {e}", exc_info=True)

        self.state = AgentState.FAILED
        self._emit_event(
            execution_id=request.execution_id,
            correlation_id=request.correlation_id,
            event_name=AgentEventName.AGENT_FAILED,
            message=f"Agent {self.role.value} failed completely: {last_error}"
        )
        return AgentResponse(
            execution_id=request.execution_id,
            correlation_id=request.correlation_id,
            status=AgentState.FAILED,
            error_message=last_error
        )

    @abc.abstractmethod
    async def _execute_internal(self, request: AgentRequest) -> Dict[str, Any]:
        """Internal operation flow override."""
        pass
