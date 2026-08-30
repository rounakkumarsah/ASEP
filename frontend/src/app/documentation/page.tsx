"use client";

import * as React from "react";
import Link from "next/link";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import {
  Book,
  Code,
  Shield,
  Cpu,
  Layers,
  Database,
  Key,
  FolderGit,
  Workflow,
  Menu,
  X,
  ChevronRight,
  Rocket,
  FlaskConical,
  Brain,
  Terminal,
  BarChart3,
  BookOpen,
  Users,
  CreditCard,
  Search,
  Settings,
  CheckCircle2,
  FileText,
  Globe,
  Zap,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

interface SidebarItem {
  name: string;
  id: string;
  icon: React.ReactNode;
}

interface SidebarGroup {
  title: string;
  items: SidebarItem[];
}

export default function DocumentationPage() {
  const [activeSection, setActiveSection] = React.useState("what-is-asep");
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = React.useState(false);

  const docGroups: SidebarGroup[] = [
    {
      title: "Introduction",
      items: [
        { name: "What is ASEP?", id: "what-is-asep", icon: <Book className="h-4 w-4" /> },
        { name: "Why ASEP Exists", id: "why-asep", icon: <Zap className="h-4 w-4" /> },
        { name: "Who Should Use ASEP", id: "who-uses-asep", icon: <Users className="h-4 w-4" /> },
        { name: "Architecture Overview", id: "architecture", icon: <Layers className="h-4 w-4" /> },
      ],
    },
    {
      title: "Getting Started",
      items: [
        { name: "Sign Up & Log In", id: "signup", icon: <Key className="h-4 w-4" /> },
        { name: "Control Plane", id: "control-plane", icon: <Cpu className="h-4 w-4" /> },
        { name: "Create a Project", id: "projects", icon: <FolderGit className="h-4 w-4" /> },
      ],
    },
    {
      title: "Platform Features",
      items: [
        { name: "Knowledge Base", id: "knowledge", icon: <BookOpen className="h-4 w-4" /> },
        { name: "Agent Playground", id: "playground", icon: <Terminal className="h-4 w-4" /> },
        { name: "Active Sessions", id: "sessions", icon: <Rocket className="h-4 w-4" /> },
        { name: "Memory Workspace", id: "memory", icon: <Brain className="h-4 w-4" /> },
        { name: "Governance & HITL", id: "governance", icon: <Shield className="h-4 w-4" /> },
        { name: "Audit Log", id: "audit", icon: <FileText className="h-4 w-4" /> },
        { name: "Evaluation Suite", id: "evaluation", icon: <FlaskConical className="h-4 w-4" /> },
        { name: "Telemetry Metrics", id: "metrics", icon: <BarChart3 className="h-4 w-4" /> },
        { name: "API Keys", id: "api-keys", icon: <Key className="h-4 w-4" /> },
      ],
    },
    {
      title: "AI Tools",
      items: [
        { name: "Deep Research Swarm", id: "research", icon: <Search className="h-4 w-4" /> },
        { name: "Developer Copilot", id: "copilot", icon: <Code className="h-4 w-4" /> },
      ],
    },
    {
      title: "Account & Billing",
      items: [
        { name: "Settings", id: "settings", icon: <Settings className="h-4 w-4" /> },
        { name: "Pricing Plans", id: "pricing", icon: <CreditCard className="h-4 w-4" /> },
      ],
    },
    {
      title: "API Reference",
      items: [
        { name: "REST API Overview", id: "api-overview", icon: <Globe className="h-4 w-4" /> },
        { name: "Authentication Endpoints", id: "auth-endpoints", icon: <Key className="h-4 w-4" /> },
        { name: "Workflow Examples", id: "workflows", icon: <Workflow className="h-4 w-4" /> },
      ],
    },
  ];

  React.useEffect(() => {
    const sectionIds = docGroups.flatMap((g) => g.items.map((i) => i.id));
    const observers: IntersectionObserver[] = [];

    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      const observer = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActiveSection(id); },
        { rootMargin: "-30% 0px -60% 0px" }
      );
      observer.observe(el);
      observers.push(observer);
    });

    return () => observers.forEach((o) => o.disconnect());
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setIsMobileDrawerOpen(false);
  };

  const SidebarContent = () => (
    <nav className="space-y-6 px-2 py-4">
      {docGroups.map((group) => (
        <div key={group.title}>
          <p className="text-[10px] font-bold uppercase tracking-widest text-[#667085] font-mono px-2 mb-2">
            {group.title}
          </p>
          <ul className="space-y-0.5">
            {group.items.map((item) => (
              <li key={item.id}>
                <button
                  onClick={() => scrollTo(item.id)}
                  className={`flex items-center w-full gap-2.5 px-2.5 py-1.5 rounded-md text-xs font-mono transition-all text-left ${
                    activeSection === item.id
                      ? "bg-[#111720] text-[#22D3EE] border-l-2 border-[#22D3EE] pl-2 font-semibold"
                      : "text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720]/60"
                  }`}
                >
                  <span className={activeSection === item.id ? "text-[#22D3EE]" : "text-[#667085]"}>
                    {item.icon}
                  </span>
                  {item.name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  );

  return (
    <div className="flex min-h-screen flex-col bg-[#090B0F] text-[#F5F7FA]">
      <LandingNavbar />

      {/* Mobile Drawer Toggle */}
      <div className="lg:hidden fixed bottom-6 right-6 z-50">
        <button
          onClick={() => setIsMobileDrawerOpen(!isMobileDrawerOpen)}
          className="p-3 bg-[#22D3EE] text-[#090B0F] rounded-full shadow-lg"
        >
          {isMobileDrawerOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Sidebar Drawer */}
      <AnimatePresence>
        {isMobileDrawerOpen && (
          <motion.div
            initial={{ x: "-100%" }}
            animate={{ x: 0 }}
            exit={{ x: "-100%" }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed inset-y-0 left-0 z-40 w-72 bg-[#0D1117] border-r border-[#202833] overflow-y-auto pt-20"
          >
            <SidebarContent />
          </motion.div>
        )}
      </AnimatePresence>

      <main className="flex-1 pt-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex gap-8 relative">

            {/* Desktop Sidebar */}
            <aside className="hidden lg:block w-64 shrink-0">
              <div className="sticky top-24 h-[calc(100vh-6rem)] overflow-y-auto border border-[#202833] bg-[#0D1117] rounded-xl">
                <SidebarContent />
              </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 min-w-0 py-10 space-y-24">

              {/* ─── WHAT IS ASEP ─── */}
              <section id="what-is-asep" className="scroll-mt-28">
                <div className="inline-flex items-center gap-2 text-[10px] font-mono font-bold uppercase tracking-widest text-[#22D3EE] bg-[#22D3EE]/10 border border-[#22D3EE]/20 px-3 py-1 rounded-full mb-4">
                  Introduction
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight text-[#F5F7FA] font-mono mb-4">
                  What is ASEP?
                </h1>
                <p className="text-[#9CA6B5] text-base leading-relaxed mb-6">
                  <strong className="text-[#F5F7FA]">ASEP (Autonomous Software Engineering Platform)</strong> is a full-stack, enterprise-grade platform that orchestrates teams of AI agents to <strong className="text-[#22D3EE]">autonomously plan, write, review, test, and deploy software</strong>.
                </p>
                <p className="text-[#9CA6B5] leading-relaxed mb-6">
                  Think of it as a <strong className="text-[#F5F7FA]">mission control center</strong> where you define what you want built, and ASEP&apos;s agent collective takes care of building it — from writing code and running security checks to seeking human approval before making any dangerous change.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8">
                  {[
                    { icon: <Cpu className="h-5 w-5" />, title: "Multi-Agent Orchestration", desc: "LangGraph-powered agent collectives that plan, execute, and verify autonomously." },
                    { icon: <Shield className="h-5 w-5" />, title: "Enterprise Governance", desc: "Human-in-the-Loop gates that pause agents before any destructive or irreversible action." },
                    { icon: <Brain className="h-5 w-5" />, title: "Persistent Memory", desc: "4-tier cognitive memory: working, episodic, semantic, and procedural — across every session." },
                  ].map((card) => (
                    <div key={card.title} className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                      <div className="text-[#22D3EE] mb-2">{card.icon}</div>
                      <h4 className="text-sm font-bold font-mono text-[#F5F7FA] mb-1">{card.title}</h4>
                      <p className="text-[11px] text-[#9CA6B5] leading-relaxed">{card.desc}</p>
                    </div>
                  ))}
                </div>
              </section>

              {/* ─── WHY ASEP ─── */}
              <section id="why-asep" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Zap className="h-7 w-7 text-[#22D3EE]" /> Why ASEP Exists
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-6">
                  Modern engineers spend more time on <strong className="text-[#F5F7FA]">repetitive, low-creativity tasks</strong> — debugging, writing boilerplate, reviewing PRs — than on high-value architecture work. AI coding assistants exist, but they only <em>suggest</em> code. A human still has to copy-paste, run, test, debug, and iterate.
                </p>
                <p className="text-[#9CA6B5] leading-relaxed mb-8">
                  ASEP eliminates the copy-paste loop entirely by deploying agents that execute code in real sandboxes, run tests, and verify their own output.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm font-mono border-collapse">
                    <thead>
                      <tr className="border-b border-[#202833]">
                        <th className="text-left py-2 px-4 text-[#667085] text-xs uppercase">Traditional AI Assistant</th>
                        <th className="text-left py-2 px-4 text-[#22D3EE] text-xs uppercase">ASEP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ["Suggests code in a chat", "Executes code in a real sandbox"],
                        ["Human must test manually", "Agents run tests automatically"],
                        ["No memory between sessions", "Persistent multi-tier memory"],
                        ["No governance", "Policy-enforced HITL gates"],
                        ["No audit trail", "Immutable audit log with full trace"],
                        ["Single model", "Multi-agent orchestrated collectives"],
                      ].map(([before, after], i) => (
                        <tr key={i} className="border-b border-[#202833]/50 hover:bg-[#111720]/30">
                          <td className="py-2.5 px-4 text-[#9CA6B5] text-xs">❌ {before}</td>
                          <td className="py-2.5 px-4 text-[#2DD4A3] text-xs">✅ {after}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* ─── WHO USES ASEP ─── */}
              <section id="who-uses-asep" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Users className="h-7 w-7 text-[#22D3EE]" /> Who Should Use ASEP
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { role: "Solo Developers", desc: "Automate repetitive coding tasks, debug errors with the AI Copilot, and run deep research swarms on technical topics." },
                    { role: "Engineering Teams", desc: "Share governance workspace, collaborative knowledge base, audit logs, and multi-agent code reviews across the team." },
                    { role: "Tech Leads / Architects", desc: "Define high-level goals, let agents handle implementation, and review diffs via the HITL approval queue before merging." },
                    { role: "DevOps Engineers", desc: "Monitor agent session telemetry, track CPU/memory, manage API keys with scope controls, and integrate with CI/CD." },
                    { role: "Enterprise Compliance", desc: "Full immutable audit trail, policy-enforced action gating, SSO (SAML/OIDC), and air-gapped deployment options." },
                    { role: "Researchers", desc: "Run autonomous deep research swarms powered by DuckDuckGo + Gemini synthesis and export reports as Markdown." },
                  ].map((item) => (
                    <div key={item.role} className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                      <h4 className="text-sm font-bold font-mono text-[#22D3EE] mb-1">{item.role}</h4>
                      <p className="text-xs text-[#9CA6B5] leading-relaxed">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </section>

              {/* ─── ARCHITECTURE ─── */}
              <section id="architecture" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Layers className="h-7 w-7 text-[#22D3EE]" /> Architecture Overview
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-6">
                  ASEP is a full-stack platform deployed on Vercel (frontend + serverless Python functions) with a PostgreSQL (Neon), Redis, Qdrant, and Neo4j backend.
                </p>
                <div className="bg-[#0D1117] border border-[#202833] rounded-xl p-6 font-mono text-xs text-[#9CA6B5] leading-relaxed space-y-2">
                  <div>👤 <span className="text-[#F5F7FA]">User</span> → 🌐 <span className="text-[#22D3EE]">Next.js Frontend (Vercel)</span></div>
                  <div className="pl-6">→ ⚡ <span className="text-[#22D3EE]">FastAPI Backend (Python 3.12)</span></div>
                  <div className="pl-12">→ 🐘 PostgreSQL (Neon) — users, projects, audit logs</div>
                  <div className="pl-12">→ ⚡ Redis — caching, rate limiting, token revocation</div>
                  <div className="pl-12">→ 🤖 <span className="text-[#2DD4A3]">LangGraph Agent Collective</span></div>
                  <div className="pl-20">→ 📦 Isolated Sandbox Executor</div>
                  <div className="pl-20">→ 🔍 Qdrant Vector Store (RAG Memory)</div>
                  <div className="pl-20">→ 🕸️ Neo4j Knowledge Graph</div>
                  <div className="pl-20">→ ✨ Google Gemini LLM</div>
                  <div className="pl-12">→ 🛡️ <span className="text-[#F05252]">HITL Governance Gate</span> → back to User for approval</div>
                  <div className="pl-12">→ 📊 Prometheus Metrics → Telemetry Dashboard</div>
                </div>
              </section>

              {/* ─── SIGN UP ─── */}
              <section id="signup" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Key className="h-7 w-7 text-[#22D3EE]" /> Sign Up & Log In
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  ASEP is live at <Link href="https://asep-ai.vercel.app" target="_blank" className="text-[#22D3EE] hover:underline">asep-ai.vercel.app</Link>. No installation required.
                </p>
                <div className="space-y-4">
                  {[
                    { step: "1", title: "Register", desc: "Go to /signup. Enter your workspace name, full name, email, and password. OAuth via GitHub or Google is also supported." },
                    { step: "2", title: "Verify Email", desc: "Check your inbox for a verification email. Click the link to activate your account." },
                    { step: "3", title: "Log In", desc: "Go to /login. Enter your credentials or use GitHub/Google OAuth." },
                    { step: "4", title: "Onboarding", desc: "You'll land on the Control Plane overview. Follow the 6-item checklist to initialize your workspace." },
                  ].map((s) => (
                    <div key={s.step} className="flex gap-4 p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                      <span className="flex-shrink-0 h-7 w-7 rounded-full bg-[#22D3EE]/10 border border-[#22D3EE]/30 text-[#22D3EE] text-xs font-bold font-mono flex items-center justify-center">{s.step}</span>
                      <div>
                        <h4 className="text-sm font-bold font-mono text-[#F5F7FA] mb-1">{s.title}</h4>
                        <p className="text-xs text-[#9CA6B5] leading-relaxed">{s.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* ─── CONTROL PLANE ─── */}
              <section id="control-plane" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Cpu className="h-7 w-7 text-[#22D3EE]" /> Control Plane
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  Your mission control dashboard at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/overview</code>. Shows real-time telemetry, system health, and your onboarding progress checklist.
                </p>
                <div className="bg-[#0D1117] border border-[#202833] rounded-xl p-5 space-y-3">
                  <p className="text-xs font-mono font-bold text-[#667085] uppercase tracking-wider">Pipeline Onboarding Checklist</p>
                  {["Create Project", "Create Agent", "Upload Knowledge", "Start Playground Chat", "Run Evaluation", "View Telemetry Metrics"].map((item, i) => (
                    <div key={i} className="flex items-center gap-3 text-xs text-[#9CA6B5]">
                      <CheckCircle2 className="h-4 w-4 text-[#202833]" />
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </section>

              {/* ─── PROJECTS ─── */}
              <section id="projects" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <FolderGit className="h-7 w-7 text-[#22D3EE]" /> Projects
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">Projects are isolated workspaces at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/projects</code>. Every agent session, knowledge upload, and API key is scoped to a project.</p>
                <div className="space-y-3">
                  <div className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                    <h4 className="text-sm font-bold font-mono text-[#22D3EE] mb-2">Creating a Project</h4>
                    <ol className="list-decimal list-inside space-y-1 text-xs text-[#9CA6B5]">
                      <li>Click <strong className="text-[#F5F7FA]">Create Project</strong> (top-right button).</li>
                      <li>Enter a name (e.g. <em>E-Commerce Backend Refactor</em>) and optional description.</li>
                      <li>Click <strong className="text-[#F5F7FA]">Create</strong>. It appears in the list immediately.</li>
                    </ol>
                  </div>
                  <div className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                    <h4 className="text-sm font-bold font-mono text-[#22D3EE] mb-2">Managing Projects</h4>
                    <ul className="list-disc list-inside space-y-1 text-xs text-[#9CA6B5]">
                      <li>Use the search bar to filter by name or description.</li>
                      <li>Projects show an <strong className="text-[#2DD4A3]">Active</strong> badge when running.</li>
                      <li>Delete a project using the 🗑️ icon — this is irreversible.</li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* ─── KNOWLEDGE BASE ─── */}
              <section id="knowledge" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <BookOpen className="h-7 w-7 text-[#22D3EE]" /> Knowledge Base
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  A vector-embedded document store at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/knowledge</code> powered by <strong className="text-[#F5F7FA]">Qdrant</strong>. Agents search this knowledge base for relevant context when executing tasks.
                </p>
                <div className="space-y-3">
                  <div className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                    <h4 className="text-sm font-bold font-mono text-[#22D3EE] mb-2">Uploading a Document</h4>
                    <ol className="list-decimal list-inside space-y-1 text-xs text-[#9CA6B5]">
                      <li>Click <strong className="text-[#F5F7FA]">Upload Document</strong>.</li>
                      <li>Enter a Document Title (e.g. <em>API Security Policy v2</em>).</li>
                      <li>Paste Markdown or text content into the textarea.</li>
                      <li>Click <strong className="text-[#F5F7FA]">Index Document</strong> — it is chunked and embedded into Qdrant.</li>
                    </ol>
                  </div>
                  <div className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                    <h4 className="text-sm font-bold font-mono text-[#22D3EE] mb-2">What to Upload</h4>
                    <ul className="list-disc list-inside space-y-1 text-xs text-[#9CA6B5]">
                      <li>Architecture RFCs and design documents</li>
                      <li>API contracts and OpenAPI specs</li>
                      <li>Coding standards and style guides</li>
                      <li>Security policies and compliance checklists</li>
                      <li>Post-mortems and runbooks</li>
                    </ul>
                  </div>
                </div>
              </section>

              {/* ─── PLAYGROUND ─── */}
              <section id="playground" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Terminal className="h-7 w-7 text-[#22D3EE]" /> Agent Playground
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  An interactive AI sandbox at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/playground</code> for directly chatting with AI models connected to your ASEP infrastructure.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {[
                    { name: "Code Review", desc: "Perform a security audit on a code block you paste." },
                    { name: "SQL Optimization", desc: "Rewrite slow subqueries into optimized high-performance JOINs." },
                    { name: "Unit Test Writer", desc: "Auto-generate comprehensive pytest functions for a FastAPI route." },
                  ].map((t) => (
                    <div key={t.name} className="p-4 bg-[#0D1117] border border-[#22D3EE]/20 rounded-xl">
                      <h4 className="text-xs font-bold font-mono text-[#22D3EE] mb-1">{t.name}</h4>
                      <p className="text-[11px] text-[#9CA6B5] leading-relaxed">{t.desc}</p>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-[#667085] mt-4 font-mono">Configuration: Model (gemini-1.5-pro), Temperature (0.0–1.0), Max Tokens (default 2048)</p>
              </section>

              {/* ─── SESSIONS ─── */}
              <section id="sessions" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Rocket className="h-7 w-7 text-[#22D3EE]" /> Active Sessions
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed">
                  A real-time monitor at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/sessions</code> showing all currently running autonomous agent execution sessions. Each session card shows status (Running / Paused / Awaiting Approval), active agent count, task description, and start time. Click <strong className="text-[#F5F7FA]">New Session</strong> to start a new agent execution. Click <strong className="text-[#F5F7FA]">Refresh</strong> to poll for updated state.
                </p>
              </section>

              {/* ─── MEMORY ─── */}
              <section id="memory" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Brain className="h-7 w-7 text-[#22D3EE]" /> Memory Workspace
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  A visual explorer at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/memory</code> of the platform&apos;s 4-tier cognitive memory architecture.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono border-collapse">
                    <thead>
                      <tr className="border-b border-[#202833]">
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Tab</th>
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Memory Type</th>
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">What it Stores</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ["Working Memory", "Short-term, in-session", "Current task state, intermediate variables"],
                        ["Episodic Memory", "Medium-term", "Records of past agent sessions — what was done, when, by whom"],
                        ["Semantic Memory", "Long-term, factual", "Domain knowledge, architecture facts, learned patterns"],
                        ["Procedural Memory", "Long-term, behavioral", "How-to knowledge — step-by-step agent procedures"],
                      ].map(([tab, type, what], i) => (
                        <tr key={i} className="border-b border-[#202833]/50 hover:bg-[#111720]/30">
                          <td className="py-2 px-3 text-[#22D3EE]">{tab}</td>
                          <td className="py-2 px-3 text-[#9CA6B5]">{type}</td>
                          <td className="py-2 px-3 text-[#9CA6B5]">{what}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* ─── GOVERNANCE ─── */}
              <section id="governance" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Shield className="h-7 w-7 text-[#22D3EE]" /> Governance & HITL Approvals
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  The Human-in-the-Loop (HITL) safety system at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/approvals</code>. Before executing any high-risk action, agents automatically <strong className="text-[#F5F7FA]">pause and request human approval</strong>.
                </p>
                <div className="bg-[#0D1117] border border-[#F05252]/20 rounded-xl p-5 font-mono text-xs text-[#9CA6B5] space-y-1 mb-4">
                  <p className="text-[#667085]">{/* Example Pending Approval Request */}</p>
                  <p><span className="text-[#22D3EE]">session_id:</span> sess_hitl_9021</p>
                  <p><span className="text-[#22D3EE]">tool_name:</span> filesystem_write</p>
                  <p><span className="text-[#22D3EE]">args:</span> {"{ path: \"/etc/hosts\", content: \"127.0.0.1 custom\" }"}</p>
                  <p><span className="text-[#22D3EE]">status:</span> <span className="text-[#F05252]">PENDING</span></p>
                  <p><span className="text-[#22D3EE]">notes:</span> Policy violation: Root directory write restriction</p>
                </div>
                <p className="text-xs text-[#9CA6B5]">
                  You can <strong className="text-[#2DD4A3]">Approve</strong>, <strong className="text-[#F05252]">Reject</strong>, or <strong className="text-[#F05252]">Escalate</strong> each request. Code changes display a <strong className="text-[#F5F7FA]">Monaco Diff Viewer</strong> showing exactly what the agent wants to modify.
                </p>
              </section>

              {/* ─── AUDIT ─── */}
              <section id="audit" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <FileText className="h-7 w-7 text-[#22D3EE]" /> Audit Log
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  An <strong className="text-[#F5F7FA]">immutable, tamper-proof chronological log</strong> at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/audit</code> of every action taken by every agent, user, and system component.
                </p>
                <p className="text-xs text-[#9CA6B5]">Each entry contains: <span className="text-[#F5F7FA]">Actor Type, Actor ID, Action, Resource, Outcome, Severity, IP Address, Timestamp</span>. You can search, filter by actor type, and export the full log for compliance.</p>
              </section>

              {/* ─── EVALUATION ─── */}
              <section id="evaluation" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <FlaskConical className="h-7 w-7 text-[#22D3EE]" /> Evaluation Suite
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  A benchmark runner at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/evaluation</code> that measures agent accuracy against standardized test suites.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono border-collapse">
                    <thead>
                      <tr className="border-b border-[#202833]">
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Dataset</th>
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Cases</th>
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Purpose</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-[#202833]/50">
                        <td className="py-2 px-3 text-[#22D3EE]">humaneval_python_sast</td>
                        <td className="py-2 px-3 text-[#9CA6B5]">164</td>
                        <td className="py-2 px-3 text-[#9CA6B5]">Code generation accuracy & security static analysis</td>
                      </tr>
                      <tr className="border-b border-[#202833]/50">
                        <td className="py-2 px-3 text-[#22D3EE]">agent_governance_policy_suite</td>
                        <td className="py-2 px-3 text-[#9CA6B5]">52</td>
                        <td className="py-2 px-3 text-[#9CA6B5]">Policy compliance & HITL trigger correctness</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              {/* ─── METRICS ─── */}
              <section id="metrics" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <BarChart3 className="h-7 w-7 text-[#22D3EE]" /> Telemetry Metrics
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  A real-time operational dashboard at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/metrics</code> powered by Prometheus. <strong className="text-[#F5F7FA]">Auto-refreshes every 5 seconds.</strong>
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {["Total Requests", "Average Latency (ms)", "Error Rate", "Active Sessions", "Pending Tasks", "CPU & Memory Usage"].map((m) => (
                    <div key={m} className="p-3 bg-[#0D1117] border border-[#202833] rounded-lg text-xs font-mono text-[#9CA6B5]">{m}</div>
                  ))}
                </div>
              </section>

              {/* ─── API KEYS ─── */}
              <section id="api-keys" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Key className="h-7 w-7 text-[#22D3EE]" /> API Keys
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  Manage programmatic access tokens at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/api-keys</code> for integrating ASEP into CI/CD pipelines, IDEs, or automation scripts.
                </p>
                <div className="bg-[#0D1117] border border-[#202833] rounded-xl p-4 font-mono text-xs">
                  <p className="text-[#667085] mb-2">{/* Creating a Key */}</p>
                  <ol className="list-decimal list-inside space-y-1 text-[#9CA6B5]">
                    <li>Click <span className="text-[#F5F7FA]">Create API Key</span>.</li>
                    <li>Enter a name (e.g. <span className="text-[#22D3EE]">GitHub Actions CI</span>).</li>
                    <li>Select the Project scope.</li>
                    <li>Click Create. <span className="text-[#F05252]">⚠️ Copy the full key immediately — shown only once!</span></li>
                  </ol>
                </div>
              </section>

              {/* ─── RESEARCH ─── */}
              <section id="research" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Search className="h-7 w-7 text-[#22D3EE]" /> Deep Research Swarm
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  An autonomous research agent at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/research</code> using DuckDuckGo search + web scraping + Google Gemini synthesis.
                </p>
                <div className="space-y-3">
                  <div className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl text-xs text-[#9CA6B5]">
                    <ol className="list-decimal list-inside space-y-1">
                      <li>Enter a topic (e.g. <em>Qdrant vs Pinecone for production RAG</em>).</li>
                      <li>Select research depth: Light / Medium / Deep.</li>
                      <li>Click <strong className="text-[#F5F7FA]">Run Research Swarm</strong>.</li>
                      <li>A formatted report with summary and sources appears.</li>
                      <li>Click <strong className="text-[#F5F7FA]">Export Markdown</strong> to download as <code>.md</code>.</li>
                    </ol>
                  </div>
                  <div className="p-3 bg-[#F05252]/5 border border-[#F05252]/20 rounded-xl text-xs font-mono text-[#9CA6B5]">
                    ⚠️ <strong className="text-[#F5F7FA]">Rate Limit:</strong> Free tier = 10 queries/day. Pro = unlimited.
                  </div>
                </div>
              </section>

              {/* ─── COPILOT ─── */}
              <section id="copilot" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Code className="h-7 w-7 text-[#22D3EE]" /> Developer Copilot
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  A multimodal AI debugging assistant at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/copilot</code>. Paste error text <strong className="text-[#F5F7FA]">or upload a screenshot</strong> — the Copilot diagnoses the root cause and provides a working code fix.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                    <h4 className="text-xs font-bold font-mono text-[#22D3EE] mb-2">Method 1: Paste Error Text</h4>
                    <p className="text-xs text-[#9CA6B5]">Use quick templates (TypeError, NullPointer, Async Timeout) or paste your own stack trace. Click <strong className="text-[#F5F7FA]">Solve Error</strong>.</p>
                  </div>
                  <div className="p-4 bg-[#0D1117] border border-[#202833] rounded-xl">
                    <h4 className="text-xs font-bold font-mono text-[#22D3EE] mb-2">Method 2: Upload Screenshot</h4>
                    <p className="text-xs text-[#9CA6B5]">Upload a screenshot of your terminal or IDE. Gemini Vision API extracts and analyzes the error — no typing required.</p>
                  </div>
                </div>
              </section>

              {/* ─── SETTINGS ─── */}
              <section id="settings" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Settings className="h-7 w-7 text-[#22D3EE]" /> Settings
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  Your complete account and platform configuration hub at <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/settings</code>. Navigate tabs via URL: <code className="bg-[#111720] text-[#9CA6B5] px-1.5 py-0.5 rounded text-xs">/settings?tab=security</code>.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    ["Profile", "Update name and locale"],
                    ["Security", "View active sessions and security overview"],
                    ["Password", "Change your password"],
                    ["MFA", "Enable/disable TOTP Two-Factor Authentication"],
                    ["Organization", "View org name, plan, and team members"],
                    ["API Keys", "Manage programmatic access tokens"],
                    ["LLM Settings", "Configure AI model providers"],
                    ["Appearance", "Toggle light/dark theme"],
                  ].map(([tab, desc]) => (
                    <div key={tab} className="flex gap-3 p-3 bg-[#0D1117] border border-[#202833] rounded-lg">
                      <span className="text-xs font-bold font-mono text-[#22D3EE] w-24 shrink-0">{tab}</span>
                      <span className="text-xs text-[#9CA6B5]">{desc}</span>
                    </div>
                  ))}
                </div>
              </section>

              {/* ─── PRICING ─── */}
              <section id="pricing" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <CreditCard className="h-7 w-7 text-[#22D3EE]" /> Pricing Plans
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono border-collapse">
                    <thead>
                      <tr className="border-b border-[#202833]">
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Feature</th>
                        <th className="text-center py-2 px-3 text-[#9CA6B5] uppercase text-[10px]">Developer (Free)</th>
                        <th className="text-center py-2 px-3 text-[#22D3EE] uppercase text-[10px]">Team ($49/user/mo)</th>
                        <th className="text-center py-2 px-3 text-[#9CA6B5] uppercase text-[10px]">Enterprise (Custom)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ["Workspaces", "1 sandbox", "Unlimited", "Unlimited"],
                        ["Active Sessions", "2 max", "Unlimited", "Unlimited"],
                        ["Knowledge Base & RAG", "✅", "✅", "✅"],
                        ["Audit Logs", "❌", "✅", "✅"],
                        ["HITL Governance", "❌", "✅", "✅ custom"],
                        ["SSO (SAML/OIDC)", "❌", "❌", "✅"],
                        ["Air-gapped Deployment", "❌", "❌", "✅"],
                        ["SLA Guarantee", "❌", "❌", "✅"],
                      ].map(([feat, dev, team, ent], i) => (
                        <tr key={i} className="border-b border-[#202833]/50 hover:bg-[#111720]/30">
                          <td className="py-2 px-3 text-[#9CA6B5]">{feat}</td>
                          <td className="py-2 px-3 text-center text-[#9CA6B5]">{dev}</td>
                          <td className="py-2 px-3 text-center text-[#22D3EE]">{team}</td>
                          <td className="py-2 px-3 text-center text-[#9CA6B5]">{ent}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Link href="/pricing" className="inline-flex items-center gap-2 mt-4 text-xs font-mono text-[#22D3EE] hover:underline">
                  View full pricing page <ChevronRight className="h-3 w-3" />
                </Link>
              </section>

              {/* ─── API OVERVIEW ─── */}
              <section id="api-overview" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Globe className="h-7 w-7 text-[#22D3EE]" /> REST API Overview
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  All endpoints are prefixed with <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">/api/v1</code>. Interactive Swagger docs are available at <Link href="/docs" className="text-[#22D3EE] hover:underline">/docs</Link>.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono border-collapse">
                    <thead>
                      <tr className="border-b border-[#202833]">
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Method</th>
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Path</th>
                        <th className="text-left py-2 px-3 text-[#667085] uppercase text-[10px]">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        ["POST", "/api/v1/auth/signup", "Register a new account"],
                        ["POST", "/api/v1/auth/login", "Login and receive JWT tokens"],
                        ["GET", "/api/v1/auth/me", "Get current user profile"],
                        ["GET", "/api/v1/projects", "List all projects"],
                        ["POST", "/api/v1/projects", "Create a new project"],
                        ["GET", "/api/v1/knowledge/documents", "Search indexed knowledge"],
                        ["POST", "/api/v1/knowledge", "Upload and index a document"],
                        ["POST", "/research/topic", "Run Research Swarm"],
                        ["POST", "/research/code_issue", "Run Developer Copilot"],
                        ["GET", "/api/v1/governance/hitl/queue", "Get HITL approval queue"],
                        ["GET", "/api/v1/audit", "Retrieve audit log entries"],
                        ["GET", "/api/v1/api-keys", "List API keys"],
                        ["POST", "/api/v1/api-keys", "Create a new API key"],
                        ["GET", "/metrics", "Prometheus metrics"],
                        ["GET", "/api/v1/health", "Health check"],
                      ].map(([method, path, desc], i) => (
                        <tr key={i} className="border-b border-[#202833]/50 hover:bg-[#111720]/30">
                          <td className={`py-2 px-3 font-bold ${method === "GET" ? "text-[#22D3EE]" : method === "POST" ? "text-[#2DD4A3]" : "text-[#F05252]"}`}>{method}</td>
                          <td className="py-2 px-3 text-[#9CA6B5]">{path}</td>
                          <td className="py-2 px-3 text-[#667085]">{desc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>

              {/* ─── AUTH ENDPOINTS ─── */}
              <section id="auth-endpoints" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Key className="h-7 w-7 text-[#22D3EE]" /> Authentication Endpoints
                </h2>
                <p className="text-[#9CA6B5] leading-relaxed mb-4">
                  All authenticated requests require a JWT Bearer token in the <code className="bg-[#111720] text-[#22D3EE] px-1.5 py-0.5 rounded text-xs">Authorization: Bearer &lt;token&gt;</code> header, or a valid httpOnly session cookie.
                </p>
                <div className="bg-[#0D1117] border border-[#202833] rounded-xl p-5 font-mono text-xs text-[#9CA6B5] space-y-3">
                  <p className="text-[#667085]">{/* Example: Register a new account */}</p>
                  <p className="text-[#2DD4A3]">POST /api/v1/auth/signup</p>
                  <pre className="text-[#9CA6B5] bg-[#111720] rounded p-3 overflow-x-auto">{`{
  "email": "jane@company.com",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "company": "Acme Corp"
}`}</pre>
                  <p className="text-[#2DD4A3]">Response 201:</p>
                  <pre className="text-[#9CA6B5] bg-[#111720] rounded p-3 overflow-x-auto">{`{
  "message": "Registration successful.",
  "user": { "id": "...", "email": "jane@company.com" }
}`}</pre>
                </div>
              </section>

              {/* ─── WORKFLOWS ─── */}
              <section id="workflows" className="scroll-mt-28">
                <h2 className="text-3xl font-bold font-mono text-[#F5F7FA] mb-4 flex items-center gap-3">
                  <Workflow className="h-7 w-7 text-[#22D3EE]" /> Common Workflow Examples
                </h2>
                <div className="space-y-6">
                  {[
                    {
                      title: "Workflow 1: Autonomous Code Review",
                      steps: [
                        "Create a Project for your codebase at /projects.",
                        "Upload architecture docs to the Knowledge Base.",
                        "Open the Playground and paste your code.",
                        "Use the 'Code Review' template prompt.",
                        "Agent reviews using your uploaded docs as context.",
                        "If it wants to apply fixes, a HITL request appears in Approvals.",
                        "Review the Monaco Diff, then Approve or Reject.",
                      ],
                    },
                    {
                      title: "Workflow 2: Debug a Production Error",
                      steps: [
                        "Open Developer Copilot at /copilot.",
                        "Take a screenshot of the error in your terminal.",
                        "Upload the screenshot — no typing required.",
                        "Gemini Vision reads the error and diagnoses the root cause.",
                        "Copy the fix code from the output panel.",
                      ],
                    },
                    {
                      title: "Workflow 3: Technical Research",
                      steps: [
                        "Go to Research at /research.",
                        "Enter your topic (e.g. 'Qdrant vs Pinecone for RAG').",
                        "Set depth to Deep.",
                        "Click Run Research Swarm.",
                        "Export the report as Markdown and share with your team.",
                      ],
                    },
                    {
                      title: "Workflow 4: Set Up CI/CD Integration",
                      steps: [
                        "Create a Project for your repository.",
                        "Navigate to API Keys.",
                        "Create a key named 'GitHub Actions'.",
                        "Add it as a GitHub Secret: ASEP_API_KEY.",
                        "Use the ASEP REST API in your pipeline to trigger evaluations.",
                      ],
                    },
                  ].map((wf) => (
                    <div key={wf.title} className="p-5 bg-[#0D1117] border border-[#202833] rounded-xl">
                      <h4 className="text-sm font-bold font-mono text-[#22D3EE] mb-3">{wf.title}</h4>
                      <ol className="list-decimal list-inside space-y-1.5 text-xs text-[#9CA6B5]">
                        {wf.steps.map((s, i) => <li key={i}>{s}</li>)}
                      </ol>
                    </div>
                  ))}
                </div>

                {/* CTA */}
                <div className="mt-16 p-8 bg-[#22D3EE]/5 border border-[#22D3EE]/20 rounded-2xl text-center">
                  <h3 className="text-xl font-bold font-mono text-[#F5F7FA] mb-2">Ready to start?</h3>
                  <p className="text-sm text-[#9CA6B5] mb-6">Create your free account and orchestrate your first autonomous agent in minutes.</p>
                  <div className="flex flex-wrap gap-3 justify-center">
                    <Link href="/signup" className="px-6 py-2.5 bg-[#22D3EE] text-[#090B0F] rounded-lg text-sm font-bold font-mono hover:bg-[#67E8F9] transition-colors">
                      Get Started Free →
                    </Link>
                    <Link href="/pricing" className="px-6 py-2.5 bg-[#111720] text-[#9CA6B5] border border-[#202833] rounded-lg text-sm font-mono hover:text-[#F5F7FA] transition-colors">
                      View Pricing
                    </Link>
                  </div>
                </div>
              </section>

            </div>
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
