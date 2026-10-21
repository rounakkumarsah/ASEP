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
            name = str(raw_name).strip().lower()
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

            # Preserve extra metadata fields from YAML
            for attr in ("author", "tags", "risk_level", "required_permissions", "schema", "prompt_template", "triggers"):
                if attr in data:
                    setattr(skill, attr, data[attr])

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
    from src.vector.embedding_service import get_embedding, get_dimension, get_provider
    from qdrant_client.http.models import PointStruct, Distance, VectorParams, PointIdsList

    provider = get_provider()
    expected_dim = get_dimension()
    logger.info("seed_embedding_provider", provider=provider, dim=expected_dim)

    collection_name = "asep_knowledge"
    client = get_qdrant_client()

    try:
        coll_exists = await client.collection_exists(collection_name=collection_name)
        if coll_exists:
            coll_info = await client.get_collection(collection_name=collection_name)
            current_size = None
            vectors_config = getattr(getattr(coll_info, "config", None), "params", None)
            vectors_param = getattr(vectors_config, "vectors", None)
            if hasattr(vectors_param, "size"):
                current_size = vectors_param.size
            elif isinstance(vectors_param, dict) and vectors_param:
                current_size = next(iter(vectors_param.values())).size

            if current_size is not None and current_size != expected_dim:
                await client.delete_collection(collection_name=collection_name)
                await client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=expected_dim, distance=Distance.COSINE),
                )
                logger.warning(
                    "qdrant_collection_recreated",
                    old_size=current_size,
                    new_size=expected_dim,
                )
        else:
            await client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=expected_dim, distance=Distance.COSINE),
            )
    except Exception as coll_exc:
        logger.warning(
            "Could not ensure Qdrant collection for seeding; Qdrant may be unavailable",
            collection=collection_name,
            error=str(coll_exc),
        )
        return

    # Delete stale zero-vectors before seeding
    try:
        offset = None
        zero_ids: list[Any] = []
        while True:
            records, next_offset = await client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_vectors=True,
            )
            for r in records:
                if r.vector is not None:
                    if isinstance(r.vector, list):
                        vec = r.vector
                    elif isinstance(r.vector, dict) and r.vector:
                        vec = next(iter(r.vector.values()))
                    else:
                        vec = list(r.vector)
                    if sum(abs(x) for x in vec) == 0:
                        zero_ids.append(r.id)
            if next_offset is None:
                break
            offset = next_offset

        if zero_ids:
            await client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(points=zero_ids),
            )
        logger.info("zero_vectors_deleted", count=len(zero_ids))
    except Exception as clean_exc:
        logger.warning(
            "Could not cleanup zero vectors from Qdrant",
            collection=collection_name,
            error=str(clean_exc),
        )

    for json_file in sorted(seed_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue

            chunk_id = str(data.get("chunk_id") or json_file.stem).strip()
            if not chunk_id:
                continue

            document_id = str(data.get("document_id") or "")
            content = str(data.get("content") or "")
            raw_metadata = data.get("metadata")
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {}

            # Deterministic UUID for Qdrant point
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

            # Idempotency check: skip if point already exists in Qdrant
            try:
                existing = await client.retrieve(collection_name=collection_name, ids=[point_id])
                if existing:
                    continue
            except Exception:
                pass

            # Generate embeddings using local/configured embedding service
            embedding = data.get("embedding")
            if (
                not embedding
                or not isinstance(embedding, list)
                or not all(isinstance(x, (int, float)) for x in embedding)
            ):
                try:
                    embedding = get_embedding(content)
                except Exception as emb_exc:
                    logger.error("Failed to generate embedding", chunk_id=chunk_id, error=str(emb_exc))
                    continue

            expected = get_dimension()
            if len(embedding) != expected:
                logger.warning("embedding_dim_mismatch", expected=expected, got=len(embedding))
                continue

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



async def seed_builtin_data(
    skills_dir: Path | None = None,
    knowledge_dir: Path | None = None,
) -> None:
    """Orchestrates seeding of both builtin skills and knowledge chunks."""
    try:
        base_dir = Path(__file__).parent
        s_dir = skills_dir if skills_dir is not None else (base_dir.parent / "skills" / "builtins")
        k_dir = knowledge_dir if knowledge_dir is not None else (base_dir / "seed")

        await seed_skills(s_dir)
        await seed_knowledge(k_dir)
    except Exception as exc:
        logger.error("Failed to seed builtin data during startup", error=str(exc))

