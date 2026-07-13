#!/bin/sh
python -c "import psycopg; conn = psycopg.connect('postgresql://asep:changeme@postgres:5432/asep'); conn.execute('DROP TABLE IF EXISTS alembic_version;'); conn.commit()"
alembic upgrade head
alembic revision --autogenerate -m 'initial_schema'
alembic upgrade head
alembic downgrade base
alembic upgrade head
