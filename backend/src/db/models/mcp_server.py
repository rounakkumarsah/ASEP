"""
ASEP — MCPServer ORM Model
==========================
Defines the ``MCPServer`` SQLAlchemy 2.0 mapped model, which stores
Model Context Protocol (MCP) server configurations per workspace.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.db.models.agent_run import TimestampMixin
from src.db.postgres import Base


class MCPServer(TimestampMixin, Base):
    """A configured Model Context Protocol (MCP) server for a workspace/project.

    Table:
        mcp_servers
    """

    __tablename__ = "mcp_servers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="UUID v4 primary key.",
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="FK to the owning Project/workspace (or null for global/default).",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Unique identifier name for this server (e.g. 'github', 'filesystem').",
    )

    transport_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="stdio",
        doc="Transport type: 'stdio' (command) or 'sse' (remote HTTP/SSE URL).",
    )

    command: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        doc="Command string for stdio transport (e.g. 'npx -y @modelcontextprotocol/server-github').",
    )

    url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        doc="Remote HTTP/SSE endpoint URL for remote transport.",
    )

    env_vars: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Encrypted environment variables token for authentication/configuration.",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this MCP server is enabled in the workspace.",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="disconnected",
        nullable=False,
        doc="Current connection status: 'connected', 'disconnected', 'error'.",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Last error message if connection or handshake failed.",
    )

    tools_cache: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Serialized JSON list of tool metadata schemas discovered from this server.",
    )
