"""
ASEP — Cypher Queries Repository
"""

# Health check query
PING_QUERY = "RETURN 1 AS ping"

# General purpose node retrieval
GET_NODE_BY_ID_QUERY = """
MATCH (n {id: $node_id})
RETURN n
"""

# Examples of queries for Phase 1.2 Ingestion
CREATE_DOCUMENT_QUERY = """
MERGE (d:Document {id: $doc_id})
SET d += $properties
RETURN d
"""

CREATE_CHUNK_QUERY = """
MERGE (c:Chunk {id: $chunk_id})
SET c += $properties
RETURN c
"""

LINK_CHUNK_TO_DOCUMENT_QUERY = """
MATCH (d:Document {id: $doc_id})
MATCH (c:Chunk {id: $chunk_id})
MERGE (d)-[r:HAS_CHUNK {index: $index}]->(c)
RETURN r
"""
