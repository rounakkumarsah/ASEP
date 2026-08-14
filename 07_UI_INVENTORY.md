# 07 — UI & Frontend Component Inventory: ASEP

This document catalogs every page, interactive dashboard view, visualization canvas, animation, and reusable component in the Next.js 15 frontend application.

---

## 1. Page Routes Inventory (38 Routes Generated)

### 1.1 Public & Marketing Pages
- `/` (Home Landing Page): Hero with 3D Neural Matrix Canvas, Social Proof Marquee, Bento Features, Interactive DAG Architecture, Integrations, Live Product Dashboard Preview, FAQ, CTA, Footer.
- `/pricing`: Interactive billing period toggle (Monthly/Yearly) with Developer, Team, and Enterprise pricing cards.
- `/documentation`: Getting started guides, architecture overview, and deployment guides.
- `/api-docs`: Interactive OpenAPI documentation explorer.
- `/architecture`: Technical whitepaper-style breakdown of the multi-agent control plane.
- `/roadmap`: Release milestones (Phase 1 through Phase 4 enterprise compliance).
- `/changelog`: Version release log with tagged commits.
- `/about`: Company mission, engineering values, and team overview.
- `/contact`: Enterprise sales and support intake form.
- `/privacy` & `/terms`: Legal terms, data retention policies, and security disclosures.

### 1.2 Authentication Pages (`app/(auth)/`)
- `/login`: Email + password authentication with Cloudflare Turnstile bot protection.
- `/signup`: User onboarding with password strength evaluation and email validation.
- `/forgot-password`: Password reset request flow.
- `/reset-password`: Token-verified credential reset form.
- `/verify-email`: Verification token landing handler.
- `/callback`: OAuth session callback handler.

### 1.3 Dashboard Suite (`app/(dashboard)/`)
- `/overview`: High-level cluster telemetry, live agent counters, and quick actions.
- `/sessions`: Filterable table of past and running agent execution sessions.
- `/sessions/[id]`: Deep-dive timeline view, subagent task execution tree, stdout logs, and artifact diff viewer.
- `/projects`: Project workspace manager with GitHub repository bindings.
- `/knowledge`: Document uploader, index sync status, and vector chunk browser.
- `/memory`: 3-tier memory inspector (Working, Semantic, Procedural).
- `/governance`: Active safety policies, rule configurations, and security triggers.
- `/approvals`: Human-in-the-Loop pending action gatekeeper with Approve/Reject actions.
- `/metrics`: Performance graphs, token consumption charts, and latency distributions.
- `/audit`: Immutable security audit log table with IP and actor filtering.
- `/billing`: Stripe subscription tier manager and invoice downloader.
- `/api-keys`: Developer API key generator, permission scoper, and revocations.
- `/settings`: Profile details, organization setup, and notification preferences.
- `/playground`: Interactive prompt execution sandbox.
- `/research`: Multi-agent research swarm inspector.
- `/evaluation`: Automated test and benchmark evaluation scoring center.
- `/copilot`: Interactive sidebar AI pairing interface.

---

## 2. Interactive Visualizations & Motion Components

1. **3D Neural Matrix Canvas** (`src/components/ui/neural-network-viz.tsx`):
   - Custom 3D orbital canvas projection with 24 floating compute nodes.
   - Non-passive touch drag with physics inertia decay.
   - Live node hovering with telemetry popovers.
   - `ResizeObserver` dynamic Retina DPR scaling (60 FPS).
2. **Interactive Architecture DAG with Animated Beams** (`src/components/landing/architecture.tsx`):
   - SVG Animated Beams connecting User &rarr; Planner &rarr; Executor &rarr; Memory &rarr; Governance &rarr; Control Plane nodes.
   - Dynamic node selection with interactive module specification inspector drawer.
3. **Infinite Logo & Testimonial Marquees** (`src/components/ui/marquee.tsx`):
   - CSS transform-based hardware-accelerated continuous scrolling with pause-on-hover.
4. **Theme Toggle** (`src/components/ui/theme-toggle.tsx`):
   - Framer Motion rotation and scale transitions between Light (Sun), Dark (Moon), and System modes without hydration mismatch.
