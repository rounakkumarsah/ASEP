"""
Alembic environment configuration.

This script handles both offline and online migrations with SQLAlchemy 2.0.
For use with asyncpg asyncio driver - migrations run synchronously via Alembic.
"""

import os

# Import Base from our ASEP database module
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.config.settings import get_settings
from src.db.models import *  # noqa: F401, F403 (Ensure all models are registered in Base.metadata)
from src.db.postgres import Base

# Get Alembic config
config = context.config

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata


def get_database_url() -> str:
    """Get database URL from environment settings.

    For Alembic migrations, we convert asyncpg:// to pg8000:// for synchronous
    operations. Alembic runs migrations synchronously to bypass AppLocker DLL blocks.
    """
    settings = get_settings()
    url = settings.DATABASE_URL
    if "postgresql+asyncpg://" in url:
        url = url.replace("postgresql+asyncpg://", "postgresql+pg8000://")
    # Strip sslmode query parameter since pg8000 expects ssl_context parameter instead
    if "sslmode=" in url:
        import re
        url = re.sub(r'[&?]sslmode=[^&]+', '', url)
    return url


def configure_naming_conventions() -> None:
    """Configure SQLAlchemy naming conventions for constraints.

    This ensures consistent constraint naming across all migrations.
    """
    naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    target_metadata.naming_convention = naming_convention


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    By skipping the Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations against a database connection.

    Args:
        connection: SQLAlchemy connection object
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create a synchronous Engine and associate
    a connection with the context. We use NullPool to avoid connection issues.
    """
    url = get_database_url()

    # Create synchronous engine with sqlalchemy.pool
    # NullPool prevents connection pooling issues during migrations
    configuration = {
        "sqlalchemy.url": url,
        "sqlalchemy.echo": False,
        "sqlalchemy.poolclass": "sqlalchemy.pool.NullPool",
    }

    import ssl
    is_remote = "localhost" not in url and "127.0.0.1" not in url and "postgres" not in url
    ssl_ctx = None
    if is_remote:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"ssl_context": ssl_ctx} if ("pg8000" in url and ssl_ctx is not None) else {}
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


# Configure naming conventions
configure_naming_conventions()

# Run migrations based on context mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


