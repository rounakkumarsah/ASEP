# ASEP — Autonomous Software Engineering Platform

ASEP is an enterprise-grade platform for deploying, managing, and evaluating autonomous AI agents. Unlike standard AI workflow tools, ASEP focuses on **production readiness** by integrating robust planning, execution memory, strict governance, and comprehensive evaluation directly into its core architecture.

## Frontend Architecture

The frontend is a strictly typed Single Page Application (SPA) built for maximum resilience, performance, and operational density.

### Tech Stack

- **Framework**: Next.js 15.1 (App Router)
- **Language**: TypeScript (Strict Mode)
- **Styling**: Tailwind CSS, shadcn/ui primitives
- **Data Fetching**: TanStack React Query v5
- **HTTP Client**: Axios (with centralized `ApiError` intercepts)
- **Icons**: Lucide React

### Folder Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router root
│   │   ├── (dashboard)/        # Authenticated Application Shell
│   │   │   ├── overview/       # Production Control Plane
│   │   │   ├── sessions/       # Live Agent Sessions
│   │   │   ├── memory/         # Tabbed Knowledge & Memory Workspace
│   │   │   └── governance/     # Human Approval & Audit Dashboard
│   │   ├── (auth)/             # JWT Authentication flows
│   │   └── page.tsx            # Enterprise Landing Page
│   ├── components/             # UI Component Library
│   │   ├── ui/                 # Reusable shadcn/ui generic primitives
│   │   ├── marketing/          # Landing page sections
│   │   ├── layout/             # Application shell, sidebar, navbar
│   │   └── dashboard/          # Specialized operational widgets
│   ├── lib/                    # Core Infrastructure
│   │   ├── api/                # Axios client, typed DTOs, React Query hooks
│   │   ├── providers/          # Global Context (Theme, Auth, Query)
│   │   └── utils.ts            # Shared utilities (e.g., cn)
```

### Data Layer & State Management

ASEP enforces a strict unidirectional API flow ensuring consistent error handling and type safety:

1. **React Query (`use-*.ts`)**: Acts as the single source of truth for all remote server state. Caching, polling, and invalidation occur here.
2. **Service Layer (`services/*.ts`)**: Strongly typed Promise wrappers mapping frontend requests to backend DTOs.
3. **Axios Client (`client.ts`)**: Global interceptors seamlessly handle JWT token injection and centralized error unrolling (401/403/404/500).

No UI component fetches data or calls `axios` directly.

### Authentication Flow

Authentication leverages a custom JWT architecture designed for future FastAPI integration.

- The global `AuthProvider` evaluates token presence upon mount.
- Protected routes in the App Router leverage layout-level redirection eliminating layout flashing.
- Intercepted `401 Unauthorized` responses gracefully wipe local tokens and push the user back to the `/login` terminal.

## Core Modules (Phase 3 Completed)

1. **Enterprise Landing Page**: A premium, conversion-optimized marketing surface (Hero, Social Proof, Interactive Architecture Previews).
2. **Application Shell**: An immutable operational sidebar framing all dashboards.
3. **Live Agent Sessions (`/sessions`)**: Granular views mapping Agent progression through distinct lifecycle states (Planning -> Executing -> Reflecting -> Completed).
4. **Memory Workspace (`/memory`)**: Tabbed interface unifying Working Memory, Episodic Memory, Semantic Knowledge, and Procedural instructions into a cohesive search interface.
5. **Governance Dashboard (`/governance`)**: A zero-trust authorization queue forcing active human-in-the-loop approvals before high-risk agent operations execute.
6. **Production Control Plane (`/overview`)**: The global telemetry hub tracking active agents, system health, and high-level audits via dense, responsive widgets.

## Build Instructions

```bash
# 1. Install dependencies
npm install

# 2. Typecheck strictly
npm run typecheck

# 3. Lint codebase
npm run lint

# 4. Generate Production Build
npm run build

# 5. Start Production Server
npm start
```

## Testing

ASEP uses **Vitest** paired with **React Testing Library** and **jsdom** for fast, reliable, and isolated testing of components, custom hooks, providers, and routing.

### Running Tests

```bash
# Run tests interactively (watch mode)
npm run test

# Run tests once
npm run test:run

# Run tests and generate coverage report
npm run test:coverage
```

### Test Architecture

- **Config**: `vitest.config.ts` handles alias path mapping (`@/*`), JSDom setup, and Vite React plugin injection.
- **Global Setup**: `src/test/setup.ts` registers global mock providers, polyfills browser APIs (like `window.matchMedia` and `ResizeObserver`), and mocks global `next/navigation` hooks using a reusable mock router spy (`mockRouter`).
- **Render Utility**: `src/test/utils.tsx` exposes `renderWithProviders`, wrapping components in `QueryClientProvider`, `ThemeProvider`, and a custom `AuthContext.Provider` (allowing custom auth states).

## Deployment Notes

- This Next.js application utilizes extensive static rendering (`SSG`) optimizations for marketing pages, paired with dynamic client-side fetching (`CSR`) for internal dashboard widgets.
- Ensure the `NEXT_PUBLIC_API_URL` environment variable is explicitly provided to point to the production FastAPI backend cluster.

---

**Status**: Frontend Implementation & Testing Suite Complete (Phase 3.9.4). Ready for Phase 3.9.5 Playwright E2E Testing.
