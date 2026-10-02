"""
Live Database Verification Script for Neo4j Cloud (Aura)
Tests connectivity, credentials, Cypher queries, GraphService, and Knowledge pathways.
"""

import asyncio
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.settings import get_settings
from src.graph.neo4j import init_neo4j, get_neo4j_driver, close_neo4j
from src.graph.health import neo4j_health_check
from src.graph.graph_service import GraphService
from src.graph.models import GraphNode, GraphRelationship


async def run_verification():
    print("=" * 60)
    print("ASEP — Neo4j Live Cloud Verification")
    print("=" * 60)

    # 1. Settings resolution
    settings = get_settings()
    print(f"[1] Configuration Loaded:")
    print(f"    NEO4J_URI: {settings.NEO4J_URI}")
    print(f"    NEO4J_USER: {settings.NEO4J_USER}")
    print(f"    NEO4J_DATABASE: {settings.NEO4J_DATABASE}")
    print(f"    AURA_INSTANCEID: {settings.AURA_INSTANCEID}")
    print(f"    AURA_INSTANCENAME: {settings.AURA_INSTANCENAME}")
    masked_pw = settings.NEO4J_PASSWORD[:4] + "..." + settings.NEO4J_PASSWORD[-4:] if len(settings.NEO4J_PASSWORD) > 8 else "***"
    print(f"    NEO4J_PASSWORD: {masked_pw}")

    # 2. Driver Connectivity Check
    print("\n[2] Initializing Neo4j Driver (init_neo4j)...")
    await init_neo4j()
    driver = get_neo4j_driver()
    await driver.verify_connectivity()
    print("    [PASS] driver.verify_connectivity() succeeded!")

    # 3. Health Check Verification
    print("\n[3] Running neo4j_health_check() and service.health_check()...")
    healthy = await neo4j_health_check()
    print(f"    [PASS] Global neo4j_health_check returned: {healthy}")
    assert healthy, "Neo4j health check failed!"

    # 4. GraphService Cypher Read/Write Check
    print("\n[4] Testing GraphService Operations...")
    service = GraphService(driver=driver)
    svc_healthy = await service.health_check()
    print(f"    [PASS] GraphService.health_check returned: {svc_healthy}")
    assert svc_healthy, "GraphService.health_check failed!"

    # Ping
    ping_result = await service.execute_read("RETURN 1 AS ping, datetime() AS now")
    print(f"    [PASS] Cypher Ping Result: {ping_result.records}")

    # Node count and Labels
    labels_res = await service.execute_read("CALL db.labels()")
    print(f"    Current DB Labels: {[r.get('label') for r in labels_res.records]}")

    # Create test nodes (GraphNode abstraction)
    test_node_1 = GraphNode(id="asep-test-node-1", labels=["AsepTestNode"], properties={"name": "Alpha", "version": "1.0"})
    test_node_2 = GraphNode(id="asep-test-node-2", labels=["AsepTestNode"], properties={"name": "Beta", "version": "1.0"})
    print("    Creating 2 test nodes...")
    await service.create_nodes([test_node_1, test_node_2])
    print("    [PASS] Created nodes.")

    # Create test relationship (GraphRelationship abstraction)
    test_rel = GraphRelationship(
        id="rel-1",
        type="CONNECTS_TO",
        start_node_id="asep-test-node-1",
        end_node_id="asep-test-node-2",
        properties={"weight": 1.0, "relationship": "depends_on"},
    )
    print("    Creating test relationship...")
    await service.create_relationships([test_rel])
    print("    [PASS] Created relationship.")

    # Query neighbors / traversal via search_related_entities (GraphRAG pathway)
    print("    Testing GraphRAG entity search / expansion...")
    related = await service.search_related_entities(entity_ids=["asep-test-node-1"], depth=1)
    print(f"    [PASS] GraphRAG 1-hop traversal: found {len(related)} related entity connections: {related}")
    assert len(related) > 0, f"Expected at least 1 related entity connection, found {len(related)}"
    assert any(r.get("target_id") == "asep-test-node-2" or r.get("source_id") == "asep-test-node-2" for r in related), "Did not find connected entity asep-test-node-2"

    # Clean up test nodes & relationships
    print("    Cleaning up test nodes...")
    await service.execute_write("MATCH (n) WHERE n.id IN $ids DETACH DELETE n", {"ids": ["asep-test-node-1", "asep-test-node-2"]})

    # Clean up any scratch edge file if present
    edge_file = os.path.join(os.path.dirname(__file__), "test_edge.py")
    if os.path.exists(edge_file):
        os.remove(edge_file)
    
    # Confirm clean
    verify_del = await service.execute_read("MATCH (n) WHERE n.id IN $ids RETURN count(n) AS remaining", {"ids": ["asep-test-node-1", "asep-test-node-2"]})
    remaining = verify_del.records[0].get("remaining", 0)
    print(f"    [PASS] Test nodes deleted. Remaining test node count: {remaining}")
    assert remaining == 0, f"Expected 0 test nodes, found {remaining}"

    # 5. Clean close
    await close_neo4j()
    print("\n[5] Neo4j connection pool cleanly closed.")
    print("\n" + "=" * 60)
    print("ALL NEO4J LIVE VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_verification())
