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

# Example queries placeholder for future phases (Phase 1.1)
# 
# MERGE_DOCUMENT_NODE_QUERY = ...
# MERGE_CHUNK_NODE_QUERY = ...
# LINK_CHUNK_TO_DOCUMENT_QUERY = ...
