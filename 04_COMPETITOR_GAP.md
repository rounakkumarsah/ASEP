# 04 — Competitor Gap Analysis & Strategic Moats: ASEP

**Benchmarked Systems**: OpenHands (All-Hands AI), Devin (Cognition), Claude Code (Anthropic), Cursor, Windsurf (Codeium), LangGraph Platform, CrewAI Enterprise, Bolt.new, Lovable.

---

## 1. Feature Separation Matrix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       COMPETITIVE FEATURE GAP MATRIX                                            │
├─────────────────────┬──────────────────┬─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│ Capability          │ ASEP (Current)   │ OpenHands       │ Devin           │ Claude Code      │ Cursor / IDEs   │
├─────────────────────┼──────────────────┼─────────────────┼─────────────────┼──────────────────┼─────────────────┤
│ Docker Sandbox      │ ✅ Implemented   │ ✅ Implemented  │ ✅ Cloud VM     │ ❌ Host Run      │ ❌ Host Run     │
│ 3-Tier Memory Graph │ ✅ Implemented   │ ❌ Flat Vector  │ ❌ Proprietary  │ ❌ Sliding Ctx   │ ❌ Vector Index │
│ HITL Policy Gates   │ ✅ Implemented   │ 🟡 Basic Pause  │ 🟡 Chat Pause   │ 🟡 Manual Prompt │ 🟡 Accept/Reject│
│ Interactive Web PTY │ 🔴 Missing       │ ✅ Implemented  │ ✅ Implemented  │ ✅ CLI Terminal  │ ✅ Native IDE   │
│ In-Browser Code Diff│ 🔴 Missing       │ ✅ Implemented  │ ✅ Implemented  │ ❌ CLI Text Diff │ ✅ Native IDE   │
│ GitHub App Auto-PR  │ 🔴 Missing       │ ✅ Implemented  │ ✅ Implemented  │ 🟡 Via CLI Push  │ ❌ N/A          │
│ VS Code Extension   │ 🔴 Missing       │ 🟡 Basic Plugin │ ❌ Web Only     │ ❌ CLI Only      │ ✅ Built-in IDE │
│ Claude 3.5 Sonnet   │ 🔴 Missing       │ ✅ Supported    │ ✅ Supported    │ ✅ Native Engine │ ✅ Supported    │
└─────────────────────┴──────────────────┴─────────────────┴─────────────────┴──────────────────┴─────────────────┘
```

---

## 2. Strategic Moats of ASEP

1. **Deterministic Multi-Tier Graph Memory (Qdrant + Neo4j)**: Unlike OpenHands and CrewAI which rely on flat vector memory or short-term context, ASEP maps code AST relationships into Neo4j graph nodes.
2. **Local-First Air-Gapped Security**: Native Ollama provider running alongside local Docker sandboxes allows enterprise air-gapped operations with zero data leakage.
3. **Rigorous Cryptographic HITL Governance**: Fine-grained risk policies (`Low` to `Critical`) with cryptographic resume tokens and SLA tracking.
