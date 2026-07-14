"""
ASEP — LangGraph Runtime Health Check
"""

import logging

from src.runtime.checkpoints import CheckpointManager
from src.runtime.edges import EdgeRegistry
from src.runtime.graph import StateGraphWrapper
from src.runtime.nodes import NodeRegistry

logger = logging.getLogger(__name__)


async def runtime_health_check() -> bool:
    """Verifies that the LangGraph runtime compiler and state checkpointers are functional.
    
    Returns:
        True if basic state workflow graphs can compile successfully, False otherwise.
    """
    try:
        nodes = NodeRegistry()
        edges = EdgeRegistry()
        checkpoints = CheckpointManager()
        
        # Dummy callbacks to verify graph compilation pathways
        nodes.register("start", lambda x: {})
        nodes.register("process", lambda x: {})
        nodes.register("validate", lambda x: {})
        nodes.register("end", lambda x: {})
        
        edges.register("human_validation_router", lambda x: "end")
        
        wrapper = StateGraphWrapper(
            node_registry=nodes,
            edge_registry=edges,
            checkpointer=checkpoints.get_checkpointer()
        )
        wrapper.assemble_default_flow()
        wrapper.compile()
        return True
    except Exception as e:
        logger.warning(f"LangGraph runtime health check failed: {e}")
        return False
