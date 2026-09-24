"""
ASEP — Autonomous Documentation Crawler & Knowledge Base
=========================================================
Crawls official documentation sources for detected stack/product types,
chunks content, indexes with TF-IDF cosine similarity, and exposes a
vector-searchable knowledge base with 7-day TTL caching.

No external embedding API calls — uses stdlib math + TF-IDF so the
entire module works offline, on Windows, with no GPU.
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Documentation source registry
# Maps detected product_type / stack keywords → list of official doc URLs
# ---------------------------------------------------------------------------
DOC_SOURCE_REGISTRY: dict[str, list[str]] = {
    # Python web frameworks
    "fastapi": [
        "https://fastapi.tiangolo.com/tutorial/",
        "https://fastapi.tiangolo.com/tutorial/first-steps/",
        "https://fastapi.tiangolo.com/tutorial/path-params/",
        "https://fastapi.tiangolo.com/tutorial/query-params/",
        "https://fastapi.tiangolo.com/tutorial/body/",
        "https://fastapi.tiangolo.com/tutorial/dependencies/",
        "https://fastapi.tiangolo.com/tutorial/security/",
    ],
    "flask": [
        "https://flask.palletsprojects.com/en/stable/quickstart/",
        "https://flask.palletsprojects.com/en/stable/tutorial/",
    ],
    "django": [
        "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
        "https://docs.djangoproject.com/en/stable/topics/http/views/",
        "https://docs.djangoproject.com/en/stable/ref/models/",
    ],
    # JavaScript / TypeScript frontend
    "react": [
        "https://react.dev/learn",
        "https://react.dev/reference/react",
        "https://react.dev/learn/state-a-components-memory",
    ],
    "nextjs": [
        "https://nextjs.org/docs/getting-started/installation",
        "https://nextjs.org/docs/app/building-your-application/routing",
        "https://nextjs.org/docs/app/building-your-application/data-fetching",
    ],
    "vue": [
        "https://vuejs.org/guide/introduction.html",
        "https://vuejs.org/guide/essentials/reactivity-fundamentals.html",
    ],
    "svelte": [
        "https://svelte.dev/docs/introduction",
        "https://svelte.dev/docs/svelte-components",
    ],
    # Backend / API
    "api": [
        "https://fastapi.tiangolo.com/tutorial/",
        "https://fastapi.tiangolo.com/tutorial/first-steps/",
        "https://fastapi.tiangolo.com/tutorial/path-params/",
        "https://fastapi.tiangolo.com/tutorial/body/",
        "https://fastapi.tiangolo.com/tutorial/dependencies/",
    ],
    # Generic web-app / app / website
    "web-app": [
        "https://react.dev/learn",
        "https://fastapi.tiangolo.com/tutorial/",
    ],
    "app": [
        "https://react.dev/learn",
        "https://fastapi.tiangolo.com/tutorial/",
    ],
    "website": [
        "https://nextjs.org/docs/getting-started/installation",
        "https://nextjs.org/docs/app/building-your-application/routing",
    ],
    "bot": [
        "https://fastapi.tiangolo.com/tutorial/",
        "https://docs.python-telegram-bot.org/en/stable/",
    ],
    # AI / ML
    "ai_agent": [
        "https://python.langchain.com/docs/concepts/",
        "https://python.langchain.com/docs/how_to/",
        "https://fastapi.tiangolo.com/tutorial/",
    ],
    "agentic_ai": [
        "https://python.langchain.com/docs/concepts/",
        "https://python.langchain.com/docs/how_to/",
    ],
    "ai_automation": [
        "https://python.langchain.com/docs/concepts/",
        "https://fastapi.tiangolo.com/tutorial/",
    ],
    # Package registries / version lookup
    "npm": [
        "https://docs.npmjs.com/about-npm",
        "https://docs.npmjs.com/cli/v10/commands/npm-install",
    ],
    "pip": [
        "https://pip.pypa.io/en/stable/",
        "https://pypi.org/",
    ],
}

# Fallback version hints for common packages (refreshed from docs when crawled)
_KNOWN_STABLE_VERSIONS: dict[str, str] = {
    "fastapi": "0.115.x",
    "react": "18.x",
    "nextjs": "14.x",
    "django": "5.x",
    "flask": "3.x",
    "vue": "3.x",
}


# ---------------------------------------------------------------------------
# HTML → plain text stripper (stdlib only)
# ---------------------------------------------------------------------------
class _HTMLTextExtractor(HTMLParser):
    """Strips all HTML tags and collects visible text content."""

    SKIP_TAGS = frozenset({"script", "style", "nav", "footer", "head", "meta", "link"})

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth: int = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data.strip():
            self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text using stdlib HTMLParser."""
    extractor = _HTMLTextExtractor()
    try:
        extractor.feed(html)
    except Exception:
        pass
    text = extractor.get_text()
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class DocChunk:
    """A single chunk of crawled documentation."""

    url: str
    text: str
    tokens: int
    product_type: str
    project_id: str
    crawled_at: datetime = field(default_factory=datetime.utcnow)
    chunk_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "text": self.text[:300],  # truncate for SSE display
            "tokens": self.tokens,
            "product_type": self.product_type,
            "project_id": self.project_id,
            "crawled_at": self.crawled_at.isoformat(),
            "chunk_index": self.chunk_index,
        }


@dataclass
class KnowledgeBaseIndex:
    """In-memory TF-IDF index over crawled documentation chunks."""

    chunks: list[DocChunk] = field(default_factory=list)
    # TF-IDF vectors: chunk_index → {term: tfidf_score}
    tfidf_vectors: list[dict[str, float]] = field(default_factory=list)
    # IDF scores: term → idf
    idf: dict[str, float] = field(default_factory=dict)
    crawled_at: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# TF-IDF helpers
# ---------------------------------------------------------------------------
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "with", "by", "as", "be", "was", "are",
    "this", "that", "from", "which", "you", "we", "can", "has",
    "have", "will", "not", "but", "if", "so", "do", "get", "use",
    "used", "also", "more", "than", "when", "what", "how",
})


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer, lowercased, stop-words removed."""
    tokens = re.findall(r"[a-z_][a-z0-9_\.]{1,40}", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) >= 2]


def _compute_tf(tokens: list[str]) -> dict[str, float]:
    counter = Counter(tokens)
    total = len(tokens) or 1
    return {term: count / total for term, count in counter.items()}


def _build_idf(all_token_lists: list[list[str]]) -> dict[str, float]:
    N = len(all_token_lists) or 1
    doc_freq: Counter[str] = Counter()
    for tokens in all_token_lists:
        for term in set(tokens):
            doc_freq[term] += 1
    return {term: math.log((N + 1) / (df + 1)) + 1.0 for term, df in doc_freq.items()}


def _tfidf_vector(tf: dict[str, float], idf: dict[str, float]) -> dict[str, float]:
    return {term: tf_val * idf.get(term, 1.0) for term, tf_val in tf.items()}


def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    dot = sum(vec_a.get(t, 0.0) * vec_b.get(t, 0.0) for t in vec_b)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values())) or 1.0
    norm_b = math.sqrt(sum(v * v for v in vec_b.values())) or 1.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# DocCrawler
# ---------------------------------------------------------------------------
_TTL_DAYS = 7
_CHUNK_MAX_TOKENS = 400
_HTTP_TIMEOUT = 15.0


class DocCrawler:
    """
    Autonomous documentation crawler and in-memory knowledge base.

    Usage::

        crawler = DocCrawler()
        chunks = await crawler.crawl_and_index("fastapi", project_id="run-123")
        results = crawler.query("how to create a route with path parameters", "fastapi")
    """

    def __init__(self) -> None:
        # Cache key: f"{project_id}:{product_type}" → KnowledgeBaseIndex
        self._index: dict[str, KnowledgeBaseIndex] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_cache_fresh(self, project_id: str, product_type: str) -> bool:
        """Return True if cached docs are within the 7-day TTL."""
        key = self._cache_key(project_id, product_type)
        if key not in self._index:
            return False
        kb = self._index[key]
        if not kb.chunks:
            return False
        age = datetime.utcnow() - kb.crawled_at
        return age < timedelta(days=_TTL_DAYS)

    async def crawl_and_index(
        self,
        product_type: str,
        project_id: str,
        urls: list[str] | None = None,
    ) -> list[DocChunk]:
        """
        Crawl documentation URLs, chunk, embed, and store in index.
        Returns all chunks produced.
        """
        resolved_urls = urls or DOC_SOURCE_REGISTRY.get(product_type, [])
        if not resolved_urls:
            logger.warning("[DocCrawler] No doc sources found for product_type=%s", product_type)
            return []

        logger.info(
            "[DocCrawler] Crawling %d URLs for product_type=%s, project_id=%s",
            len(resolved_urls),
            product_type,
            project_id,
        )

        all_chunks: list[DocChunk] = []
        for url in resolved_urls:
            try:
                html = await self._fetch(url)
                text = _html_to_text(html)
                chunks = self._chunk(text, url=url, product_type=product_type, project_id=project_id)
                all_chunks.extend(chunks)
                logger.info("[DocCrawler] %s -> %d chunks", url, len(chunks))
            except Exception as exc:
                logger.warning("[DocCrawler] Failed to fetch %s: %s", url, exc)
                # Produce a fallback chunk with known pattern hints
                fallback = self._fallback_chunk(url, product_type, project_id)
                if fallback:
                    all_chunks.append(fallback)

        if not all_chunks:
            logger.warning("[DocCrawler] No chunks produced for %s — using static fallback", product_type)
            all_chunks = self._static_fallback_chunks(product_type, project_id)

        # Build TF-IDF index
        key = self._cache_key(project_id, product_type)
        self._index[key] = self._build_index(all_chunks)
        logger.info("[DocCrawler] Index built: %d chunks for key=%s", len(all_chunks), key)
        return all_chunks

    def query(
        self,
        query_text: str,
        product_type: str,
        project_id: str = "global",
        top_k: int = 5,
    ) -> list[DocChunk]:
        """
        Return top-k chunks most similar to query_text via cosine similarity.
        Falls back to empty list if nothing is indexed.
        """
        key = self._cache_key(project_id, product_type)
        # Try project-scoped index first, then global
        kb = self._index.get(key) or self._index.get(self._cache_key("global", product_type))
        if kb is None or not kb.chunks:
            return []

        q_tokens = _tokenize(query_text)
        q_tf = _compute_tf(q_tokens)
        q_vec = _tfidf_vector(q_tf, kb.idf)

        scored = [
            (chunk, _cosine_similarity(q_vec, vec))
            for chunk, vec in zip(kb.chunks, kb.tfidf_vectors)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored[:top_k] if score > 0.0]

    async def refresh(self, project_id: str, product_type: str) -> list[DocChunk]:
        """Evict stale cache and re-crawl."""
        key = self._cache_key(project_id, product_type)
        if key in self._index:
            del self._index[key]
            logger.info("[DocCrawler] Cache evicted for key=%s", key)
        return await self.crawl_and_index(product_type, project_id)

    def get_cached_chunks(self, project_id: str, product_type: str) -> list[DocChunk]:
        """Return cached chunks without re-crawling."""
        key = self._cache_key(project_id, product_type)
        kb = self._index.get(key)
        return kb.chunks if kb else []

    def get_stack_versions(self, product_type: str) -> dict[str, str]:
        """Return known stable version hints for the product type's stack."""
        versions: dict[str, str] = {}
        for keyword, version in _KNOWN_STABLE_VERSIONS.items():
            if keyword in product_type or product_type in keyword:
                versions[keyword] = version
        # Always include the product type itself if known
        if product_type in _KNOWN_STABLE_VERSIONS:
            versions[product_type] = _KNOWN_STABLE_VERSIONS[product_type]
        return versions

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(project_id: str, product_type: str) -> str:
        return f"{project_id}:{product_type}"

    async def _fetch(self, url: str) -> str:
        """Async HTTP GET with timeout. Returns raw HTML string."""
        try:
            import httpx
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=_HTTP_TIMEOUT,
                headers={"User-Agent": "ASEP-DocCrawler/1.0 (autonomous research agent)"},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except ImportError:
            # Fallback to urllib if httpx not available
            import urllib.request
            with urllib.request.urlopen(url, timeout=int(_HTTP_TIMEOUT)) as resp:
                return resp.read().decode("utf-8", errors="replace")

    def _chunk(
        self,
        text: str,
        url: str,
        product_type: str,
        project_id: str,
    ) -> list[DocChunk]:
        """
        Split text into chunks of at most _CHUNK_MAX_TOKENS tokens,
        splitting on paragraph or sentence boundaries.
        """
        if not text.strip():
            return []

        # Split on double-newline (paragraph) or ". " or "\n"
        paragraphs = re.split(r"\n{2,}|\.\s+(?=[A-Z])", text)
        chunks: list[DocChunk] = []
        current_parts: list[str] = []
        current_tokens = 0
        now = datetime.utcnow()

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            # Rough token estimate: 1 token ≈ 4 characters
            para_tokens = max(1, len(para) // 4)

            if current_tokens + para_tokens > _CHUNK_MAX_TOKENS and current_parts:
                chunk_text = " ".join(current_parts)
                chunks.append(DocChunk(
                    url=url,
                    text=chunk_text,
                    tokens=current_tokens,
                    product_type=product_type,
                    project_id=project_id,
                    crawled_at=now,
                    chunk_index=len(chunks),
                ))
                current_parts = []
                current_tokens = 0

            current_parts.append(para)
            current_tokens += para_tokens

        if current_parts:
            chunk_text = " ".join(current_parts)
            chunks.append(DocChunk(
                url=url,
                text=chunk_text,
                tokens=current_tokens,
                product_type=product_type,
                project_id=project_id,
                crawled_at=now,
                chunk_index=len(chunks),
            ))

        return chunks

    def _build_index(self, chunks: list[DocChunk]) -> KnowledgeBaseIndex:
        """Build TF-IDF vectors for all chunks."""
        all_token_lists = [_tokenize(c.text) for c in chunks]
        idf = _build_idf(all_token_lists)
        tfidf_vectors = [
            _tfidf_vector(_compute_tf(tokens), idf)
            for tokens in all_token_lists
        ]
        return KnowledgeBaseIndex(
            chunks=chunks,
            tfidf_vectors=tfidf_vectors,
            idf=idf,
            crawled_at=datetime.utcnow(),
        )

    def _fallback_chunk(self, url: str, product_type: str, project_id: str) -> DocChunk | None:
        """Produce a minimal fallback chunk from known pattern hints when HTTP fails."""
        hints = _STATIC_PATTERN_HINTS.get(product_type, [])
        if not hints:
            return None
        text = " ".join(hints[:3])
        return DocChunk(
            url=url,
            text=text,
            tokens=len(text) // 4,
            product_type=product_type,
            project_id=project_id,
            crawled_at=datetime.utcnow(),
        )

    def _static_fallback_chunks(self, product_type: str, project_id: str) -> list[DocChunk]:
        """Return hardcoded pattern hints as chunks when all HTTP fetches fail."""
        hints = _STATIC_PATTERN_HINTS.get(product_type, _STATIC_PATTERN_HINTS.get("api", []))
        now = datetime.utcnow()
        chunks: list[DocChunk] = []
        for i, hint in enumerate(hints):
            chunks.append(DocChunk(
                url=f"static://patterns/{product_type}/{i}",
                text=hint,
                tokens=max(1, len(hint) // 4),
                product_type=product_type,
                project_id=project_id,
                crawled_at=now,
                chunk_index=i,
            ))
        return chunks


# ---------------------------------------------------------------------------
# Static pattern hints (used as fallback when HTTP crawl fails)
# These reflect current stable API patterns for common frameworks.
# ---------------------------------------------------------------------------
_STATIC_PATTERN_HINTS: dict[str, list[str]] = {
    "fastapi": [
        "from fastapi import FastAPI, HTTPException, Depends, status\n"
        "from fastapi.security import OAuth2PasswordBearer\n"
        "app = FastAPI(title='My API', version='1.0.0')\n"
        "@app.get('/items/{item_id}', response_model=ItemResponse)\n"
        "async def read_item(item_id: int, db: Session = Depends(get_db)):\n"
        "    item = await db.get(Item, item_id)\n"
        "    if not item:\n"
        "        raise HTTPException(status_code=404, detail='Item not found')\n"
        "    return item",

        "from pydantic import BaseModel, Field\n"
        "class Item(BaseModel):\n"
        "    name: str = Field(..., min_length=1, max_length=100)\n"
        "    price: float = Field(..., gt=0)\n"
        "    description: str | None = None\n"
        "@app.post('/items/', response_model=Item, status_code=status.HTTP_201_CREATED)\n"
        "async def create_item(item: Item, db: AsyncSession = Depends(get_async_db)):\n"
        "    db.add(item)\n"
        "    await db.commit()\n"
        "    return item",

        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/users', tags=['users'])\n"
        "@router.get('/{user_id}')\n"
        "async def get_user(user_id: int, current_user: User = Depends(get_current_user)):\n"
        "    return current_user\n"
        "app.include_router(router)\n"
        "# Use lifespan for startup/shutdown events (FastAPI 0.93+):\n"
        "from contextlib import asynccontextmanager\n"
        "@asynccontextmanager\n"
        "async def lifespan(app: FastAPI):\n"
        "    # startup\n"
        "    yield\n"
        "    # shutdown\n"
        "app = FastAPI(lifespan=lifespan)",

        "# Dependency injection for database sessions\n"
        "from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker\n"
        "engine = create_async_engine(DATABASE_URL, echo=False)\n"
        "AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)\n"
        "async def get_async_db():\n"
        "    async with AsyncSessionLocal() as session:\n"
        "        yield session",

        "# Modern FastAPI security pattern (0.100+)\n"
        "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials\n"
        "security = HTTPBearer()\n"
        "@app.get('/protected')\n"
        "async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(security)):\n"
        "    token = credentials.credentials\n"
        "    # validate token\n"
        "    return {'user': 'authenticated'}",
    ],
    "react": [
        "// Modern React 18+ with hooks\n"
        "import { useState, useEffect, useCallback } from 'react';\n"
        "function MyComponent({ id }: { id: number }) {\n"
        "  const [data, setData] = useState<Item | null>(null);\n"
        "  useEffect(() => {\n"
        "    fetch(`/api/items/${id}`)\n"
        "      .then(r => r.json())\n"
        "      .then(setData);\n"
        "  }, [id]);\n"
        "  return <div>{data?.name}</div>;\n"
        "}",

        "// React Server Components (Next.js App Router / React 18)\n"
        "// No 'use client' needed for server components\n"
        "async function Page({ params }: { params: { id: string } }) {\n"
        "  const data = await fetch(`/api/items/${params.id}`);\n"
        "  const item = await data.json();\n"
        "  return <div>{item.name}</div>;\n"
        "}",
    ],
    "nextjs": [
        "// Next.js 14 App Router — page.tsx\n"
        "export default async function Page({ params, searchParams }: {\n"
        "  params: { slug: string };\n"
        "  searchParams: { [key: string]: string | undefined };\n"
        "}) {\n"
        "  return <main><h1>{params.slug}</h1></main>;\n"
        "}\n"
        "// Metadata API (Next.js 13+)\n"
        "export const metadata = { title: 'My App', description: '...' };",

        "// Next.js API Route (app/api/route.ts)\n"
        "import { NextRequest, NextResponse } from 'next/server';\n"
        "export async function GET(req: NextRequest) {\n"
        "  return NextResponse.json({ message: 'ok' });\n"
        "}\n"
        "export async function POST(req: NextRequest) {\n"
        "  const body = await req.json();\n"
        "  return NextResponse.json(body, { status: 201 });\n"
        "}",
    ],
    "django": [
        "# Django 5.x views with class-based API\n"
        "from django.views import View\n"
        "from django.http import JsonResponse\n"
        "from django.contrib.auth.mixins import LoginRequiredMixin\n"
        "class ItemView(LoginRequiredMixin, View):\n"
        "    def get(self, request, pk):\n"
        "        item = Item.objects.get(pk=pk)\n"
        "        return JsonResponse({'name': item.name})\n"
        "    def post(self, request):\n"
        "        import json\n"
        "        data = json.loads(request.body)\n"
        "        item = Item.objects.create(**data)\n"
        "        return JsonResponse({'id': item.pk}, status=201)",
    ],
    "flask": [
        "# Flask 3.x — modern patterns\n"
        "from flask import Flask, jsonify, request, abort\n"
        "from flask.views import MethodView\n"
        "app = Flask(__name__)\n"
        "class ItemAPI(MethodView):\n"
        "    def get(self, item_id):\n"
        "        item = Item.query.get_or_404(item_id)\n"
        "        return jsonify(item.to_dict())\n"
        "    def post(self):\n"
        "        data = request.get_json()\n"
        "        item = Item(**data)\n"
        "        db.session.add(item)\n"
        "        db.session.commit()\n"
        "        return jsonify(item.to_dict()), 201\n"
        "app.add_url_rule('/items/<int:item_id>', view_func=ItemAPI.as_view('item_api'))",
    ],
    "vue": [
        "// Vue 3 Composition API\n"
        "<script setup lang='ts'>\n"
        "import { ref, computed, onMounted } from 'vue';\n"
        "const count = ref(0);\n"
        "const doubled = computed(() => count.value * 2);\n"
        "onMounted(() => console.log('mounted'));\n"
        "</script>",
    ],
    "api": [
        "from fastapi import FastAPI, HTTPException, Depends, status\n"
        "from fastapi.security import OAuth2PasswordBearer\n"
        "app = FastAPI(title='My API', version='1.0.0')\n"
        "@app.get('/items/{item_id}')\n"
        "async def read_item(item_id: int, db: AsyncSession = Depends(get_async_db)):\n"
        "    item = await db.get(Item, item_id)\n"
        "    if not item:\n"
        "        raise HTTPException(status_code=404, detail='Item not found')\n"
        "    return item",

        "from pydantic import BaseModel, Field\n"
        "class ItemCreate(BaseModel):\n"
        "    name: str = Field(..., min_length=1)\n"
        "    price: float = Field(..., gt=0)\n"
        "@app.post('/items/', status_code=status.HTTP_201_CREATED)\n"
        "async def create_item(item: ItemCreate, db: AsyncSession = Depends(get_async_db)):\n"
        "    new_item = Item(**item.model_dump())\n"
        "    db.add(new_item)\n"
        "    await db.commit()\n"
        "    return new_item",
    ],
    "web-app": [
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\nasync def root():\n    return {'message': 'Hello World'}",
        "import { useState } from 'react';\nfunction App() {\n  const [state, setState] = useState(null);\n  return <div>{state}</div>;\n}",
    ],
    "app": [
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\nasync def root():\n    return {'message': 'Hello World'}",
    ],
    "website": [
        "// Next.js 14 App Router layout.tsx\n"
        "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
        "  return <html lang='en'><body>{children}</body></html>;\n"
        "}",
    ],
    "bot": [
        "from telegram.ext import Application, CommandHandler\n"
        "from telegram import Update\n"
        "from telegram.ext import ContextTypes\n"
        "async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:\n"
        "    await update.message.reply_text('Hello!')\n"
        "app = Application.builder().token(TOKEN).build()\n"
        "app.add_handler(CommandHandler('start', start))\n"
        "app.run_polling()",
    ],
    "ai_agent": [
        "from langchain_core.messages import HumanMessage, AIMessage\n"
        "from langgraph.graph import StateGraph, END\n"
        "from langgraph.checkpoint.memory import MemorySaver\n"
        "workflow = StateGraph(AgentState)\n"
        "workflow.add_node('agent', call_agent)\n"
        "workflow.set_entry_point('agent')\n"
        "workflow.add_edge('agent', END)\n"
        "memory = MemorySaver()\n"
        "app = workflow.compile(checkpointer=memory)",
    ],
}


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
doc_crawler = DocCrawler()
