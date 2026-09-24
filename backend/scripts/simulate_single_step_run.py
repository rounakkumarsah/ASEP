"""
ASEP Simulation Script: Full Run in ONE /step call
Verifies that execute_step loops graph.astream until completion,
collecting all events across all graph nodes in a single /step call.
"""

import asyncio
import os
import sys
import time
import uuid
from unittest.mock import AsyncMock, MagicMock

# Ensure backend root is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

os.environ["AI_PROVIDER_PRIORITY"] = "mock"

from src.runtime.runtime import LangGraphRuntime


async def main():
    print("=" * 60)
    print("ASEP LOCAL SIMULATION: Full Run in ONE execute_step Call")
    print("=" * 60)

    mock_mem = MagicMock()
    mock_mem.working.set_state = AsyncMock()
    mock_mem.working.get_state = AsyncMock(return_value=None)
    runtime = LangGraphRuntime(mock_mem)

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    goal = "Build a REST API backend with FastAPI"

    print("Initiating run:")
    print(f"  run_id:    {run_id}")
    print(f"  thread_id: {thread_id}")
    print(f"  goal:      {goal}")
    print("-" * 60)

    start = time.perf_counter()
    step_result = await runtime.execute_step(
        run_id=run_id,
        thread_id=thread_id,
        goal=goal,
        is_first=True,
    )
    elapsed = time.perf_counter() - start

    events = step_result.get("events", [])
    status = step_result.get("status")

    print(f"Step Result Status: {status}")
    print(f"Total Events Yielded: {len(events)}")
    print(f"Execution Time: {elapsed:.2f}s")
    print("-" * 60)
    print("Per-Step Nodes Executed in This Single /step Call:")

    nodes_visited = []
    for idx, event in enumerate(events, 1):
        for node_name in event.keys():
            nodes_visited.append(node_name)
            node_data = event[node_name]
            node_status = node_data.get("status", "N/A") if isinstance(node_data, dict) else "N/A"
            current_phase = node_data.get("current_phase", node_name) if isinstance(node_data, dict) else node_name
            print(f"  [{idx:02d}] Node: {node_name:<20} Phase: {current_phase:<20} Status: {node_status}")

    print("-" * 60)
    print(f"Unique nodes executed ({len(set(nodes_visited))}): {list(dict.fromkeys(nodes_visited))}")

    # Inspect state checkpointer
    state = await runtime.graph.aget_state({"configurable": {"thread_id": thread_id}})
    pending_nodes = list(state.next) if state else []
    print(f"Final State Pending Nodes: {pending_nodes}")
    print(f"Workflow Finished in Single Step: {status == 'done' and len(pending_nodes) == 0}")

    assert status == "done", f"Expected status 'done', got {status}"
    assert len(pending_nodes) == 0, f"Expected 0 pending nodes, got {pending_nodes}"
    assert len(events) > 1, f"Expected multiple events, got {len(events)}"
    print("=" * 60)
    print("SIMULATION SUCCESS: Full multi-node pipeline completed in ONE /step call!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
