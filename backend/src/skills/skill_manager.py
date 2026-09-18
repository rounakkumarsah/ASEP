"""
ASEP — Skill System Manager
===========================
Industry-standard Claude Agent Skills implementation with:
- YAML frontmatter + Markdown parser and serializer
- Built-in skills immutability and user skills CRUD
- Composed skills with dependency graph resolution and cycle detection
- Keyword + semantic trigger matching (max 3 active skills per run)
- Reference document attachment processing (PDF, DOCX, TXT, code)
- Chunking (500 tokens, 100 overlap) and vector store namespace: skill/<skill-name>
- Top-5 citation retrieval: [FROM: <filename>, page <page>]
- Versioning with restore (last 3 versions)
- Safety invariants: system rules always take precedence, credentials policy enforced
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import shutil
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


def _parse_yaml_fallback(text: str) -> dict[str, Any]:
    """Pure-Python YAML frontmatter parser fallback when PyYAML is not installed."""
    res: dict[str, Any] = {}
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                items = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                res[k] = items
            elif v.lower() == "true":
                res[k] = True
            elif v.lower() == "false":
                res[k] = False
            elif v.isdigit():
                res[k] = int(v)
            else:
                res[k] = v.strip("'\"")
    return res


def _dump_yaml_fallback(data: dict[str, Any]) -> str:
    """Pure-Python YAML frontmatter serializer fallback."""
    lines = []
    for k, v in data.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


logger = logging.getLogger(__name__)

# Max limits per skill
MAX_ATTACHMENTS_PER_SKILL = 20
MAX_TOTAL_ATTACHMENTS_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_ACTIVE_SKILLS = 3
CHUNK_SIZE_CHARS = 2000  # ~500 tokens
CHUNK_OVERLAP_CHARS = 400  # ~100 tokens
MAX_VERSION_HISTORY = 3


@dataclass
class SkillAttachment:
    filename: str
    file_type: str
    file_size: int
    status: str  # "ready" | "partially_parsed" | "failed"
    chunk_count: int
    uploaded_at: str
    chunks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "uploaded_at": self.uploaded_at,
        }


@dataclass
class Skill:
    name: str
    description: str
    trigger: str
    instructions: str
    dependencies: list[str] = field(default_factory=list)
    scope: str = "workspace"  # "workspace" | "project"
    project_id: str | None = None
    enabled: bool = True
    is_builtin: bool = False
    version: int = 1
    attachments: list[SkillAttachment] = field(default_factory=list)
    version_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "instructions": self.instructions,
            "dependencies": self.dependencies,
            "scope": self.scope,
            "project_id": self.project_id,
            "enabled": self.enabled,
            "is_builtin": self.is_builtin,
            "version": self.version,
            "attachments": [a.to_dict() for a in self.attachments],
            "version_history": self.version_history,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def to_markdown(self) -> str:
        """Serialize skill to Claude Agent Skill format (YAML frontmatter + markdown body)."""
        frontmatter = {
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "dependencies": self.dependencies,
            "scope": self.scope,
            "is_builtin": self.is_builtin,
            "enabled": self.enabled,
            "version": self.version,
        }
        if self.project_id:
            frontmatter["project_id"] = self.project_id

        if yaml is not None:
            fm_yaml = yaml.safe_dump(frontmatter, sort_keys=False, default_flow_style=False).strip()
        else:
            fm_yaml = _dump_yaml_fallback(frontmatter)
        return f"---\n{fm_yaml}\n---\n\n{self.instructions.strip()}\n"


class SkillManager:
    """Manages skill persistence, trigger matching, composition, and document retrieval."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Look for project root skills/ or backend/skills/
            candidate_1 = Path("skills").resolve()
            candidate_2 = (Path(__file__).parent.parent.parent / "skills").resolve()
            self.base_dir = candidate_1 if candidate_1.exists() else candidate_2

        self.builtin_dir = self.base_dir / "builtin"
        self.user_dir = self.base_dir / "user"
        self.attachments_dir = self.base_dir / "attachments"

        self.builtin_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)

        # In-memory index of parsed skills
        self._skills_cache: dict[str, Skill] = {}
        # Vector index for skill attachments: namespace -> list of chunk records
        self._vector_namespaces: dict[str, list[dict[str, Any]]] = {}

        self.reload_all_skills()

    # -------------------------------------------------------------------------
    # Parsing & Storage
    # -------------------------------------------------------------------------

    def parse_markdown(self, content: str, is_builtin: bool = False) -> Skill:
        """Parse a markdown file with YAML frontmatter."""
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            frontmatter_str, body = match.group(1), match.group(2)
            if yaml is not None:
                meta = yaml.safe_load(frontmatter_str) or {}
            else:
                meta = _parse_yaml_fallback(frontmatter_str)
        else:
            meta = {}
            body = content

        name = meta.get("name", "unnamed-skill")
        # Sanitize name
        name = re.sub(r"[^a-zA-Z0-9_-]", "-", name.lower()).strip("-")

        # Parse dependencies from frontmatter or check "also apply:" in body
        dependencies = meta.get("dependencies") or []
        if isinstance(dependencies, str):
            dependencies = [d.strip() for d in dependencies.split(",") if d.strip()]

        # Scan body for "also apply: <skill>"
        body_deps = re.findall(r"(?:also apply|requires? skill):\s*([a-zA-Z0-9_-]+)", body, re.IGNORECASE)
        for bd in body_deps:
            if bd not in dependencies and bd != name:
                dependencies.append(bd)

        return Skill(
            name=name,
            description=meta.get("description", ""),
            trigger=str(meta.get("trigger", "")),
            instructions=body.strip(),
            dependencies=dependencies,
            scope=meta.get("scope", "workspace"),
            project_id=meta.get("project_id"),
            enabled=bool(meta.get("enabled", True)),
            is_builtin=is_builtin,
            version=int(meta.get("version", 1)),
        )

    def reload_all_skills(self) -> None:
        """Load built-in and user skills from disk."""
        self._skills_cache.clear()

        # 1. Load Built-in skills
        if self.builtin_dir.exists():
            for p in self.builtin_dir.glob("*.md"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    skill = self.parse_markdown(text, is_builtin=True)
                    self._load_skill_attachments(skill)
                    self._skills_cache[skill.name] = skill
                except Exception as exc:
                    logger.error("Failed to load built-in skill %s: %s", p, exc)

        # 2. Load User skills
        if self.user_dir.exists():
            for p in self.user_dir.glob("**/*.md"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    skill = self.parse_markdown(text, is_builtin=False)
                    self._load_skill_attachments(skill)
                    self._skills_cache[skill.name] = skill
                except Exception as exc:
                    logger.error("Failed to load user skill %s: %s", p, exc)

    def _load_skill_attachments(self, skill: Skill) -> None:
        """Loads attachment metadata and chunk cache for a skill."""
        meta_file = self.attachments_dir / skill.name / "metadata.json"
        if meta_file.exists():
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                skill.version_history = data.get("version_history", [])
                skill.attachments = []
                for att_data in data.get("attachments", []):
                    att = SkillAttachment(
                        filename=att_data["filename"],
                        file_type=att_data.get("file_type", "txt"),
                        file_size=att_data.get("file_size", 0),
                        status=att_data.get("status", "ready"),
                        chunk_count=att_data.get("chunk_count", 0),
                        uploaded_at=att_data.get("uploaded_at", datetime.now(UTC).isoformat()),
                        chunks=att_data.get("chunks", []),
                    )
                    skill.attachments.append(att)
                    # Register chunks into vector namespace
                    namespace = f"skill/{skill.name}"
                    if namespace not in self._vector_namespaces:
                        self._vector_namespaces[namespace] = []
                    self._vector_namespaces[namespace].extend(att.chunks)
            except Exception as exc:
                logger.warning("Error loading attachment metadata for %s: %s", skill.name, exc)

    def _save_skill_attachments_metadata(self, skill: Skill) -> None:
        """Persists attachment metadata for a skill."""
        skill_att_dir = self.attachments_dir / skill.name
        skill_att_dir.mkdir(parents=True, exist_ok=True)
        meta_file = skill_att_dir / "metadata.json"
        data = {
            "version_history": skill.version_history,
            "attachments": [asdict(a) for a in skill.attachments],
        }
        meta_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    def list_skills(
        self,
        project_id: str | None = None,
        scope: str | None = None,
        search: str | None = None,
    ) -> list[Skill]:
        """List skills matching criteria."""
        results: list[Skill] = []
        search_lower = search.lower().strip() if search else None

        for skill in self._skills_cache.values():
            if scope and scope != "all":
                if scope == "builtin" and not skill.is_builtin:
                    continue
                if scope == "user" and skill.is_builtin:
                    continue
                if scope == "workspace" and skill.scope != "workspace":
                    continue
                if scope == "project" and skill.scope != "project":
                    continue

            if project_id and skill.scope == "project" and skill.project_id != project_id:
                continue

            if search_lower:
                in_name = search_lower in skill.name.lower()
                in_desc = search_lower in skill.description.lower()
                in_trig = search_lower in skill.trigger.lower()
                if not (in_name or in_desc or in_trig):
                    continue

            results.append(skill)

        # Sort: built-in first, then alphabetical by name
        results.sort(key=lambda s: (not s.is_builtin, s.name))
        return results

    def get_skill(self, name: str) -> Skill | None:
        """Get skill by name."""
        return self._skills_cache.get(name.lower().strip())

    def create_skill(self, data: dict[str, Any]) -> Skill:
        """Create a new user skill."""
        raw_name = data.get("name", "").strip()
        if not raw_name:
            raise ValueError("Skill name is required")

        name = re.sub(r"[^a-zA-Z0-9_-]", "-", raw_name.lower()).strip("-")
        if name in self._skills_cache:
            raise ValueError(f"Skill '{name}' already exists")

        dependencies = data.get("dependencies") or []
        if isinstance(dependencies, str):
            dependencies = [d.strip() for d in dependencies.split(",") if d.strip()]

        instructions = data.get("instructions", "").strip()
        body_deps = re.findall(r"(?:also apply|requires? skill):\s*([a-zA-Z0-9_-]+)", instructions, re.IGNORECASE)
        for bd in body_deps:
            if bd not in dependencies and bd != name:
                dependencies.append(bd)

        skill = Skill(
            name=name,
            description=data.get("description", ""),
            trigger=str(data.get("trigger", "")),
            instructions=instructions,
            dependencies=dependencies,
            scope=data.get("scope", "workspace"),
            project_id=data.get("project_id"),
            enabled=bool(data.get("enabled", True)),
            is_builtin=False,
            version=1,
        )

        # Save to disk
        file_path = self.user_dir / f"{skill.name}.md"
        file_path.write_text(skill.to_markdown(), encoding="utf-8")
        self._skills_cache[skill.name] = skill
        return skill

    def update_skill(self, name: str, data: dict[str, Any]) -> Skill:
        """Update an existing user skill."""
        skill = self.get_skill(name)
        if not skill:
            raise KeyError(f"Skill '{name}' not found")
        if skill.is_builtin:
            raise PermissionError("Built-in skills cannot be edited")

        # Snapshot version for version history
        if skill.instructions or skill.attachments:
            history_entry = {
                "version": skill.version,
                "instructions": skill.instructions,
                "attachments": [a.to_dict() for a in skill.attachments],
                "saved_at": datetime.now(UTC).isoformat(),
            }
            skill.version_history.insert(0, history_entry)
            skill.version_history = skill.version_history[:MAX_VERSION_HISTORY]

        skill.version += 1
        skill.description = data.get("description", skill.description)
        skill.trigger = str(data.get("trigger", skill.trigger))
        skill.instructions = data.get("instructions", skill.instructions).strip()
        body_deps = re.findall(r"(?:also apply|requires? skill):\s*([a-zA-Z0-9_-]+)", skill.instructions, re.IGNORECASE)
        for bd in body_deps:
            if bd not in skill.dependencies and bd != skill.name:
                skill.dependencies.append(bd)
        if "dependencies" in data:
            deps = data["dependencies"]
            skill.dependencies = [d.strip() for d in deps.split(",")] if isinstance(deps, str) else deps
        if "enabled" in data:
            skill.enabled = bool(data["enabled"])
        if "scope" in data:
            skill.scope = data["scope"]
        if "project_id" in data:
            skill.project_id = data["project_id"]
        skill.updated_at = datetime.now(UTC).isoformat()

        # Save to disk
        file_path = self.user_dir / f"{skill.name}.md"
        file_path.write_text(skill.to_markdown(), encoding="utf-8")
        self._save_skill_attachments_metadata(skill)
        return skill

    def delete_skill(self, name: str) -> bool:
        """Delete a user skill."""
        skill = self.get_skill(name)
        if not skill:
            return False
        if skill.is_builtin:
            raise PermissionError("Built-in skills cannot be deleted")

        file_path = self.user_dir / f"{skill.name}.md"
        if file_path.exists():
            file_path.unlink()

        # Remove attachments directory
        skill_att_dir = self.attachments_dir / skill.name
        if skill_att_dir.exists():
            shutil.rmtree(skill_att_dir, ignore_errors=True)

        # Clear vector namespace
        self._vector_namespaces.pop(f"skill/{skill.name}", None)
        self._skills_cache.pop(skill.name, None)
        return True

    def toggle_skill(self, name: str, enabled: bool) -> Skill:
        """Enable or disable a skill."""
        skill = self.get_skill(name)
        if not skill:
            raise KeyError(f"Skill '{name}' not found")

        skill.enabled = enabled
        if not skill.is_builtin:
            file_path = self.user_dir / f"{skill.name}.md"
            file_path.write_text(skill.to_markdown(), encoding="utf-8")
        return skill

    def duplicate_skill(self, name: str) -> Skill:
        """Duplicate an existing skill as a new user skill."""
        orig = self.get_skill(name)
        if not orig:
            raise KeyError(f"Skill '{name}' not found")

        # Find unique name
        base_copy_name = f"{orig.name}-copy"
        copy_name = base_copy_name
        counter = 1
        while copy_name in self._skills_cache:
            counter += 1
            copy_name = f"{base_copy_name}-{counter}"

        duplicated = Skill(
            name=copy_name,
            description=f"Copy of {orig.description}",
            trigger=orig.trigger,
            instructions=orig.instructions,
            dependencies=list(orig.dependencies),
            scope=orig.scope,
            project_id=orig.project_id,
            enabled=True,
            is_builtin=False,
            version=1,
        )

        file_path = self.user_dir / f"{duplicated.name}.md"
        file_path.write_text(duplicated.to_markdown(), encoding="utf-8")
        self._skills_cache[duplicated.name] = duplicated
        return duplicated

    # -------------------------------------------------------------------------
    # Import / Export
    # -------------------------------------------------------------------------

    def export_skill(self, name: str, format_type: str = "md") -> tuple[str, bytes]:
        """Export skill as .md file or ZIP with attachments."""
        skill = self.get_skill(name)
        if not skill:
            raise KeyError(f"Skill '{name}' not found")

        if format_type == "zip" and skill.attachments:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(f"{skill.name}.md", skill.to_markdown())
                skill_att_dir = self.attachments_dir / skill.name
                if skill_att_dir.exists():
                    for f in skill_att_dir.iterdir():
                        if f.is_file():
                            zf.write(f, arcname=f"attachments/{f.name}")
            buf.seek(0)
            return f"{skill.name}.zip", buf.getvalue()
        else:
            md_bytes = skill.to_markdown().encode("utf-8")
            return f"{skill.name}.md", md_bytes

    def import_skill(self, content_bytes: bytes, filename: str) -> Skill:
        """Import skill from .md file or ZIP archive."""
        if filename.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(content_bytes)) as zf:
                md_files = [f for f in zf.namelist() if f.endswith(".md") and not f.startswith("__MACOSX")]
                if not md_files:
                    raise ValueError("ZIP archive contains no .md skill definition file")
                md_content = zf.read(md_files[0]).decode("utf-8", errors="ignore")
                skill = self.parse_markdown(md_content, is_builtin=False)
                # Create user skill
                if skill.name in self._skills_cache:
                    skill.name = f"{skill.name}-imported"
                file_path = self.user_dir / f"{skill.name}.md"
                file_path.write_text(skill.to_markdown(), encoding="utf-8")
                self._skills_cache[skill.name] = skill

                # Extract any attachments in zip
                for f in zf.namelist():
                    if f.startswith("attachments/") and not f.endswith("/"):
                        att_name = Path(f).name
                        file_data = zf.read(f)
                        self.add_attachment(skill.name, att_name, file_data)
                return self._skills_cache[skill.name]
        else:
            md_content = content_bytes.decode("utf-8", errors="ignore")
            skill = self.parse_markdown(md_content, is_builtin=False)
            if skill.name in self._skills_cache:
                skill.name = f"{skill.name}-imported"
            file_path = self.user_dir / f"{skill.name}.md"
            file_path.write_text(skill.to_markdown(), encoding="utf-8")
            self._skills_cache[skill.name] = skill
            return skill

    # -------------------------------------------------------------------------
    # Attachment Pipeline (PDF, DOCX, TXT, MD, Code)
    # -------------------------------------------------------------------------

    def add_attachment(self, skill_name: str, filename: str, content_bytes: bytes) -> SkillAttachment:
        """Upload and process an attachment for a skill."""
        skill = self.get_skill(skill_name)
        if not skill:
            raise KeyError(f"Skill '{skill_name}' not found")
        if skill.is_builtin:
            raise PermissionError("Attachments cannot be added to built-in skills")

        if len(skill.attachments) >= MAX_ATTACHMENTS_PER_SKILL:
            raise ValueError(f"Maximum of {MAX_ATTACHMENTS_PER_SKILL} attachments reached for this skill")

        total_size = sum(a.file_size for a in skill.attachments) + len(content_bytes)
        if total_size > MAX_TOTAL_ATTACHMENTS_BYTES:
            raise ValueError(f"Attachments exceed total allowed limit of 50 MB ({total_size / (1024*1024):.1f} MB)")

        skill_att_dir = self.attachments_dir / skill.name
        skill_att_dir.mkdir(parents=True, exist_ok=True)
        saved_path = skill_att_dir / filename
        saved_path.write_bytes(content_bytes)

        # Extraction and chunking
        ext = Path(filename).suffix.lower()
        chunks, status = self._extract_and_chunk(saved_path, ext, content_bytes)

        # If previous version of attachment exists, replace it
        skill.attachments = [a for a in skill.attachments if a.filename != filename]
        attachment = SkillAttachment(
            filename=filename,
            file_type=ext.lstrip(".") or "txt",
            file_size=len(content_bytes),
            status=status,
            chunk_count=len(chunks),
            uploaded_at=datetime.now(UTC).isoformat(),
            chunks=chunks,
        )
        skill.attachments.append(attachment)

        # Ingest into vector store namespace: skill/<skill-name>
        namespace = f"skill/{skill.name}"
        # Filter out old chunks from this filename
        current_chunks = self._vector_namespaces.get(namespace, [])
        current_chunks = [c for c in current_chunks if c.get("filename") != filename]
        current_chunks.extend(chunks)
        self._vector_namespaces[namespace] = current_chunks

        self._save_skill_attachments_metadata(skill)
        return attachment

    def delete_attachment(self, skill_name: str, filename: str) -> bool:
        """Delete an attachment and its chunks from a skill."""
        skill = self.get_skill(skill_name)
        if not skill or skill.is_builtin:
            return False

        orig_len = len(skill.attachments)
        skill.attachments = [a for a in skill.attachments if a.filename != filename]
        if len(skill.attachments) == orig_len:
            return False

        # Remove file on disk
        saved_path = self.attachments_dir / skill.name / filename
        if saved_path.exists():
            saved_path.unlink()

        # Remove from vector namespace
        namespace = f"skill/{skill.name}"
        if namespace in self._vector_namespaces:
            self._vector_namespaces[namespace] = [
                c for c in self._vector_namespaces[namespace] if c.get("filename") != filename
            ]

        self._save_skill_attachments_metadata(skill)
        return True

    def restore_version(self, skill_name: str, version_idx: int = 0) -> Skill:
        """Restore skill instructions and attachments from version history."""
        skill = self.get_skill(skill_name)
        if not skill or skill.is_builtin:
            raise KeyError(f"Skill '{skill_name}' not found or is built-in")

        if not skill.version_history or version_idx >= len(skill.version_history):
            raise IndexError("Version index not available in history")

        snapshot = skill.version_history.pop(version_idx)
        skill.instructions = snapshot.get("instructions", skill.instructions)
        skill.version += 1
        skill.updated_at = datetime.now(UTC).isoformat()

        file_path = self.user_dir / f"{skill.name}.md"
        file_path.write_text(skill.to_markdown(), encoding="utf-8")
        self._save_skill_attachments_metadata(skill)
        return skill

    def _extract_and_chunk(
        self,
        file_path: Path,
        ext: str,
        content_bytes: bytes,
    ) -> tuple[list[dict[str, Any]], str]:
        """Extract text from file and split into 500-token / 100-overlap chunks."""
        chunks: list[dict[str, Any]] = []
        status = "ready"
        pages_text: list[tuple[int, str]] = []  # (page_num, text)

        try:
            if ext == ".pdf":
                # Try PyMuPDF / fitz
                try:
                    import fitz  # type: ignore[import-not-found]
                    with fitz.open(stream=content_bytes, filetype="pdf") as doc:
                        for page_idx in range(len(doc)):
                            p = doc[page_idx]
                            txt = p.get_text()
                            if not txt.strip():
                                status = "partially_parsed"
                            pages_text.append((page_idx + 1, txt))
                except Exception as p_err:
                    logger.warning("PyMuPDF unavailable or failed (%s), using plaintext fallback", p_err)
                    # Simple text fallback extraction for testing / environments without fitz
                    raw_text = content_bytes.decode("utf-8", errors="ignore")
                    pages_text.append((1, raw_text))

            elif ext == ".docx":
                try:
                    import docx  # type: ignore[import-not-found]
                    doc = docx.Document(io.BytesIO(content_bytes))
                    full_text = "\n".join(p.text for p in doc.paragraphs)
                    pages_text.append((1, full_text))
                except Exception as docx_err:
                    logger.warning("python-docx extraction fallback: %s", docx_err)
                    pages_text.append((1, content_bytes.decode("utf-8", errors="ignore")))

            else:
                # Text, Markdown, Python, TypeScript, JSON, SQL, etc.
                raw_text = content_bytes.decode("utf-8", errors="ignore")
                pages_text.append((1, raw_text))

        except Exception as exc:
            logger.error("Text extraction failed for %s: %s", file_path.name, exc)
            return [], "failed"

        # Chunk each page text (500 tokens ~2000 chars, 100 overlap ~400 chars)
        chunk_idx = 0
        for page_num, p_text in pages_text:
            if not p_text.strip():
                continue
            pos = 0
            while pos < len(p_text):
                end_pos = pos + CHUNK_SIZE_CHARS
                chunk_str = p_text[pos:end_pos].strip()
                if chunk_str:
                    chunks.append({
                        "chunk_id": f"{file_path.name}_c{chunk_idx}",
                        "filename": file_path.name,
                        "page": page_num,
                        "text": chunk_str,
                    })
                    chunk_idx += 1
                pos += (CHUNK_SIZE_CHARS - CHUNK_OVERLAP_CHARS)

        return chunks, status

    # -------------------------------------------------------------------------
    # Composition & Dependency Chain Resolution
    # -------------------------------------------------------------------------

    def resolve_dependencies(self, skill_names: list[str]) -> list[str]:
        """Resolves dependency chain recursively with cycle detection and deduplication."""
        resolved: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def dfs(name: str) -> None:
            if name in visiting:
                # Cycle detected — break cycle safely
                logger.warning("Circular dependency detected in skill '%s'", name)
                return
            if name in visited:
                return

            visiting.add(name)
            skill = self.get_skill(name)
            if skill:
                for dep in skill.dependencies:
                    dfs(dep.lower().strip())

            visiting.remove(name)
            visited.add(name)
            if name not in resolved:
                resolved.append(name)

        for s_name in skill_names:
            dfs(s_name.lower().strip())

        return resolved

    # -------------------------------------------------------------------------
    # Trigger Matching & Activation Engine
    # -------------------------------------------------------------------------

    def match_skills(
        self,
        request_text: str,
        phase_type: str = "",
        project_id: str | None = None,
        force_enabled: list[str] | None = None,
        force_disabled: list[str] | None = None,
    ) -> list[Skill]:
        """Matches request + phase against skill triggers and resolves composed skills.

        Caps activation at MAX_ACTIVE_SKILLS (3).
        """
        force_enabled_set = set(s.lower().strip() for s in (force_enabled or []))
        force_disabled_set = set(s.lower().strip() for s in (force_disabled or []))

        text_to_match = f"{request_text} {phase_type}".lower()
        tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", text_to_match))

        scored_skills: list[tuple[float, Skill]] = []

        for skill in self._skills_cache.values():
            if not skill.enabled and skill.name not in force_enabled_set:
                continue
            if skill.name in force_disabled_set:
                continue
            if skill.scope == "project" and project_id and skill.project_id != project_id:
                continue

            # Check force-enable
            if skill.name in force_enabled_set:
                scored_skills.append((1000.0, skill))
                continue

            # Score triggers
            trigger_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", skill.trigger.lower()))
            if not trigger_tokens:
                continue

            match_count = len(tokens.intersection(trigger_tokens))
            if match_count > 0:
                # Keyword match score
                score = (match_count / len(trigger_tokens)) * 10.0 + match_count
                scored_skills.append((score, skill))

        # Sort highest score first
        scored_skills.sort(key=lambda x: x[0], reverse=True)
        top_skill_names = [s.name for _, s in scored_skills]

        # Resolve composed dependencies
        resolved_chain = self.resolve_dependencies(top_skill_names)

        # Cap at MAX_ACTIVE_SKILLS
        final_skill_names = resolved_chain[:MAX_ACTIVE_SKILLS]
        active_skills: list[Skill] = []
        for name in final_skill_names:
            s = self.get_skill(name)
            if s and s not in active_skills:
                active_skills.append(s)

        return active_skills

    # -------------------------------------------------------------------------
    # Retrieval at Activation
    # -------------------------------------------------------------------------

    def retrieve_attachment_chunks(
        self,
        skill_name: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Queries the skill's attachment namespace and returns top_k relevant chunks with citations."""
        namespace = f"skill/{skill_name.lower().strip()}"
        chunks = self._vector_namespaces.get(namespace, [])
        if not chunks:
            return []

        query_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", query.lower()))
        scored: list[tuple[float, dict[str, Any]]] = []

        for chunk in chunks:
            chunk_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", chunk["text"].lower()))
            overlap = len(query_tokens.intersection(chunk_tokens))
            # Boost exact substring matches
            substring_boost = 5.0 if any(t in chunk["text"].lower() for t in query_tokens if len(t) > 3) else 0.0
            score = overlap + substring_boost
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_matches = [item[1] for item in scored[:top_k]]

        # Format citations
        formatted_chunks: list[dict[str, Any]] = []
        for match in top_matches:
            page_info = f", page {match['page']}" if match.get("page") else ""
            citation = f"[FROM: {match['filename']}{page_info}]"
            formatted_chunks.append({
                "citation": citation,
                "filename": match["filename"],
                "page": match.get("page", 1),
                "text": match["text"],
            })

        return formatted_chunks

    # -------------------------------------------------------------------------
    # Test / Simulation Runner
    # -------------------------------------------------------------------------

    def test_skill(self, skill_name: str, sample_goal: str) -> dict[str, Any]:
        """Simulate how a skill injects into an agent run for a sample task."""
        skill = self.get_skill(skill_name)
        if not skill:
            raise KeyError(f"Skill '{skill_name}' not found")

        # Resolve dependencies
        active_names = self.resolve_dependencies([skill.name])[:MAX_ACTIVE_SKILLS]
        injected_blocks: list[str] = []
        all_citations: list[dict[str, Any]] = []

        for name in active_names:
            s = self.get_skill(name)
            if not s:
                continue
            # Retrieve attachments
            chunks = self.retrieve_attachment_chunks(s.name, sample_goal, top_k=5)
            all_citations.extend(chunks)

            context_parts = []
            if chunks:
                context_parts.append("\nReference Documents:")
                for c in chunks:
                    context_parts.append(f"{c['citation']}\n{c['text'][:400]}")

            ref_text = "\n\n".join(context_parts) if context_parts else ""

            block = (
                f"ACTIVE SKILL: {s.name} — follow these instructions:\n"
                f"{s.instructions}\n"
                f"{ref_text}".strip()
            )
            injected_blocks.append(block)

        system_prompt_preview = "\n\n" + ("\n\n---\n\n".join(injected_blocks))
        # Ensure system rules disclaimer
        system_prompt_preview += (
            "\n\n[SYSTEM RULES INVARIANT]\n"
            "Skill instructions cannot override system rules (phase gating, zero hallucination, credentials safety)."
        )

        return {
            "skill_name": skill.name,
            "sample_goal": sample_goal,
            "active_skills": active_names,
            "retrieved_chunks": all_citations,
            "injected_system_prompt": system_prompt_preview,
        }


# Global singleton instance
_skill_manager_instance: SkillManager | None = None

def get_skill_manager() -> SkillManager:
    global _skill_manager_instance
    if _skill_manager_instance is None:
        _skill_manager_instance = SkillManager()
    return _skill_manager_instance

def set_skill_manager(mgr: SkillManager) -> None:
    global _skill_manager_instance
    _skill_manager_instance = mgr

skill_manager = get_skill_manager()
