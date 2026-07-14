"""
ASEP — Graph Models
"""

from typing import Any, Mapping

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Represents a generic node in the graph."""
    id: str = Field(description="Unique identifier for the node")
    labels: list[str] = Field(default_factory=list, description="Labels assigned to the node")
    properties: dict[str, Any] = Field(default_factory=dict, description="Node properties")


class GraphRelationship(BaseModel):
    """Represents a generic relationship between two nodes."""
    id: str = Field(description="Unique identifier for the relationship")
    type: str = Field(description="Relationship type")
    start_node_id: str = Field(description="ID of the starting node")
    end_node_id: str = Field(description="ID of the ending node")
    properties: dict[str, Any] = Field(default_factory=dict, description="Relationship properties")


class GraphResult(BaseModel):
    """Wrapper for structured query results."""
    records: list[Mapping[str, Any]] = Field(default_factory=list, description="List of raw records from the query")
    summary: dict[str, Any] = Field(default_factory=dict, description="Query execution summary")
