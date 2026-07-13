/**
 * ASEP — Home Page (Scaffold)
 * TODO (Phase 0.2): Replace with real dashboard showing agent runs.
 */
export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 text-zinc-100">
      <div className="text-center space-y-4">
        <div className="text-6xl font-bold tracking-tight bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
          ASEP
        </div>
        <p className="text-xl text-zinc-400">
          Autonomous Software Engineering Platform
        </p>
        <p className="text-sm text-zinc-600">
          Phase 0.1 — Scaffold · Dashboard coming in Phase 0.2
        </p>
        <div className="flex gap-4 justify-center pt-4">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 rounded-md bg-violet-600 hover:bg-violet-500 text-white text-sm font-medium transition-colors"
          >
            API Docs
          </a>
          <a
            href="http://localhost:8000/health"
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 rounded-md border border-zinc-700 hover:border-zinc-500 text-zinc-300 text-sm font-medium transition-colors"
          >
            Health
          </a>
        </div>
      </div>
    </main>
  );
}
