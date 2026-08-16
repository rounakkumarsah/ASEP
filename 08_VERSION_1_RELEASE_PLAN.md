# 08 — Version 1.0 General Availability Release Plan: ASEP

**Milestone**: ASEP v1.0 General Availability (GA)  
**Target Release**: Q4 2026

---

## 1. Release Gates & Acceptance Criteria

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ASEP v1.0 GA RELEASE GATES                      │
├───────────────────────────────────┬────────────────────────────────────┤
│ Quality Gate                      │ Acceptance Target                  │
├───────────────────────────────────┼────────────────────────────────────┤
│ 1. TypeScript Strict Check        │ 0 Errors (`tsc --noEmit`)          │
│ 2. ESLint Validation              │ 0 Errors / 0 Warnings              │
│ 3. Next.js Static Pages           │ 38/38 Routes Generated Cleanly     │
│ 4. Backend Pytest Suites          │ 100% Pass Rate across all modules  │
│ 5. Docker Single-Command Boot     │ Verified on Windows, Mac, Linux    │
│ 6. Core Provider Support          │ Gemini + OpenAI + Claude + Ollama  │
│ 7. Diff & Terminal DevEx          │ Monaco Diff + Xterm.js Embedded    │
│ 8. Security & Bot Defense         │ Turnstile + CSP + Cryptographic HITL│
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 2. Launch Sequence

1. **Phase A (Alpha Tagged Release)**: Internal benchmarking and bug bash across all 38 Next.js pages.
2. **Phase B (Public Beta)**: GitHub release with 1-command Docker quickstart, documentation site, and YouTube demo showcase.
3. **Phase C (v1.0 General Availability)**: Public launch on Hacker News, Reddit (`r/selfhosted`, `r/LocalLLaMA`), Product Hunt, and AI Engineering communities.
