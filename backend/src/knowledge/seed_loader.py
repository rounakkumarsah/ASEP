"""
ASEP — Built-in Knowledge & Skills Seed Loader
==============================================
Automatically seeds default skills and knowledge chunks on application startup.
- Skills from backend/src/skills/builtins/*.yaml -> SkillManager
- Knowledge chunks from backend/src/knowledge/seed/*.json -> Qdrant 'asep_knowledge'
"""

from __future__ import annotations

import json
from pathlib import Path
import uuid
from typing import Any

import structlog

try:
    import yaml
except ImportError:
    yaml = None

from src.skills.skill_manager import Skill, get_skill_manager

logger = structlog.get_logger(__name__)


def _parse_yaml_file(file_path: Path) -> dict[str, Any]:
    content = file_path.read_text(encoding="utf-8")
    if yaml is not None:
        return yaml.safe_load(content) or {}
    # Fallback minimal parser
    from src.skills.skill_manager import _parse_yaml_fallback
    return _parse_yaml_fallback(content)


async def seed_skills(skills_dir: Path) -> None:
    """Seed skills from YAML files into the existing SkillManager."""
    if not skills_dir.exists():
        return

    skill_mgr = get_skill_manager()

    for yaml_file in sorted(skills_dir.glob("*.yaml")):
        try:
            data = _parse_yaml_file(yaml_file)
            if not isinstance(data, dict):
                continue

            raw_name = data.get("name") or yaml_file.stem
            name = str(raw_name).strip()
            if not name:
                continue

            # Idempotency check: skip if skill already exists in SkillManager
            if skill_mgr.get_skill(name) is not None:
                continue

            triggers = data.get("triggers", [])
            if isinstance(triggers, list):
                trigger_str = " ".join(str(t) for t in triggers)
            else:
                trigger_str = str(triggers or data.get("trigger") or "")

            instructions = str(data.get("instructions", "")).strip()
            desc = str(data.get("description", "")).strip()

            skill = Skill(
                name=name,
                description=desc,
                trigger=trigger_str,
                instructions=instructions,
                dependencies=data.get("dependencies") or [],
                scope=data.get("scope", "workspace"),
                enabled=True,
                is_builtin=True,
                version=1,
            )

            # Register in SkillManager cache
            skill_mgr._skills_cache[name] = skill

            logger.info("seeded_builtin", seeded_builtin=name, type="skill", name=name)
        except Exception as exc:
            logger.error("Failed to seed builtin skill", file=str(yaml_file), error=str(exc))


async def seed_knowledge(seed_dir: Path) -> None:
    """Seed knowledge base chunks from JSON files into Qdrant collection 'asep_knowledge'."""
    if not seed_dir.exists():
        return

    from src.vector.qdrant import get_qdrant_client
    from src.vector.collections import create_collection_if_not_exists
    from src.documents.embedding_service import RuntimeEmbeddingProvider
    from qdrant_client.http.models import PointStruct

    collection_name = "asep_knowledge"
    vector_size = 1536

    client = get_qdrant_client()
    embedder = RuntimeEmbeddingProvider()

    try:
        await create_collection_if_not_exists(
            client=client,
            collection_name=collection_name,
            vector_size=vector_size,
        )
    except Exception as coll_exc:
        logger.warning(
            "Could not ensure Qdrant collection for seeding; Qdrant may be unavailable",
            collection=collection_name,
            error=str(coll_exc),
        )
        return

    for json_file in sorted(seed_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue

            chunk_id = data.get("chunk_id") or json_file.stem
            document_id = data.get("document_id", "")
            content = data.get("content", "")
            metadata = data.get("metadata", {})

            # Deterministic UUID for Qdrant point
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

            # Idempotency check: skip if point already exists in Qdrant
            try:
                existing = await client.retrieve(collection_name=collection_name, ids=[point_id])
                if existing:
                    continue
            except Exception:
                pass

            # Generate embeddings using existing embedding service
            embedding = data.get("embedding")
            if not embedding or not isinstance(embedding, list):
                try:
                    generated = await embedder.embed_documents([content])
                    embedding = generated[0] if generated else [0.0] * vector_size
                except Exception as emb_exc:
                    logger.warning("Failed to generate embedding; using zero vector fallback", error=str(emb_exc))
                    embedding = [0.0] * vector_size

            payload = {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "content": content,
                "text": content,
                **metadata,
            }

            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload,
            )

            await client.upsert(
                collection_name=collection_name,
                points=[point],
            )

            logger.info("seeded_builtin", seeded_builtin=chunk_id, type="knowledge", chunk_id=chunk_id)
        except Exception as exc:
            logger.error("Failed to seed knowledge chunk", file=str(json_file), error=str(exc))


async def seed_builtin_data() -> None:
    """Orchestrates seeding of both builtin skills and knowledge chunks."""
    base_dir = Path(__file__).parent
    skills_dir = base_dir.parent / "skills" / "builtins"
    knowledge_dir = base_dir / "seed"

    await seed_skills(skills_dir)
    await seed_knowledge(knowledge_dir)
