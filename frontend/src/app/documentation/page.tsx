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
  ChevronRight 
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
  const [activeSection, setActiveSection] = React.useState("overview");
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = React.useState(false);

  const docGroups: SidebarGroup[] = [
    {
      title: "Getting Started",
      items: [
        { name: "Overview", id: "overview", icon: <Book className="h-4 w-4" /> },
        { name: "Installation", id: "installation", icon: <Code className="h-4 w-4" /> },
        { name: "Quickstart Guide", id: "quickstart", icon: <ChevronRight className="h-4 w-4" /> },
      ],
    },
    {
      title: "Core Concepts",
      items: [
        { name: "Agent Topology", id: "topology", icon: <Cpu className="h-4 w-4" /> },
        { name: "Sandbox Security", id: "security", icon: <Shield className="h-4 w-4" /> },
        { name: "Memory Synchronization", id: "memory", icon: <Database className="h-4 w-4" /> },
      ],
    },
    {
      title: "API Reference",
      items: [
        { name: "Authentication", id: "authentication", icon: <Key className="h-4 w-4" /> },
        { name: "Workspace Control", id: "workspace", icon: <FolderGit className="h-4 w-4" /> },
        { name: "Governance Webhooks", id: "webhooks", icon: <Workflow className="h-4 w-4" /> },
      ],
    },
  ];

  // IntersectionObserver to dynamically highlight active section on scroll
  React.useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: "-25% 0px -55% 0px",
      threshold: 0.1,
    };

    const handleIntersection = (entries: IntersectionObserverEntry[]) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setActiveSection(entry.target.id);
        }
      });
    };

    const observer = new IntersectionObserver(handleIntersection, observerOptions);
    const sections = document.querySelectorAll("section[id]");
    sections.forEach((section) => observer.observe(section));

    return () => {
      sections.forEach((section) => observer.unobserve(section));
    };
  }, []);

  // Sync scroll on mount or hash change
  React.useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (hash) {
        const targetElement = document.querySelector(hash);
        if (targetElement) {
          targetElement.scrollIntoView({ behavior: "smooth" });
        }
      }
    };

    window.addEventListener("hashchange", handleHashChange);
    // Short delay to ensure browser DOM finishes rendering
    const timer = setTimeout(handleHashChange, 150);

    return () => {
      window.removeEventListener("hashchange", handleHashChange);
      clearTimeout(timer);
    };
  }, []);

  const handleLinkClick = (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    setIsMobileDrawerOpen(false);
    
    // Update hash manually in URL bar without page reload, which triggers history state change
    window.history.pushState(null, "", `#${id}`);
    
    const targetElement = document.getElementById(id);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: "smooth" });
    }
  };

  const renderSidebarContent = () => (
    <div className="space-y-6">
      {docGroups.map((group, idx) => (
        <div key={idx}>
          <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase mb-3 px-2">
            {group.title}
          </h3>
          <nav className="flex flex-col space-y-1" aria-label={`${group.title} navigation`}>
            {group.items.map((item) => {
              const isActive = activeSection === item.id;
              return (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  onClick={(e) => handleLinkClick(item.id, e)}
                  aria-current={isActive ? "page" : undefined}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                    isActive
                      ? "bg-primary/10 text-primary font-medium"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  }`}
                >
                  {item.icon}
                  <span>{item.name}</span>
                </a>
              );
            })}
          </nav>
        </div>
      ))}
    </div>
  );

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <LandingNavbar />

      {/* Floating Sticky Mobile Toggle Menu */}
      <div className="lg:hidden fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setIsMobileDrawerOpen(true)}
          className="flex items-center gap-2 px-4 py-3 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/95 transition-all outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-primary"
          aria-label="Open documentation navigation menu"
        >
          <Menu className="h-5 w-5" />
          <span className="text-sm font-semibold">Docs Menu</span>
        </button>
      </div>

      {/* Mobile Drawer Overlay / Sidebar */}
      <AnimatePresence>
        {isMobileDrawerOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileDrawerOpen(false)}
              className="lg:hidden fixed inset-0 bg-background/80 backdrop-blur-sm z-50"
            />
            <motion.div
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="lg:hidden fixed top-0 bottom-0 left-0 w-80 max-w-[85vw] bg-card border-r border-border/50 shadow-2xl p-6 overflow-y-auto z-55 flex flex-col gap-6"
            >
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold tracking-tight">ASEP Docs</span>
                <button
                  onClick={() => setIsMobileDrawerOpen(false)}
                  className="p-1 rounded-lg hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-all"
                  aria-label="Close navigation menu"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="flex-1">
                {renderSidebarContent()}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <main className="flex-1 pt-32 pb-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
            
            {/* Desktop Sidebar (Sticky) */}
            <div className="hidden lg:block">
              <aside className="sticky top-32 max-h-[calc(100vh-10rem)] overflow-y-auto pr-4 border-r border-border/20">
                {renderSidebarContent()}
              </aside>
            </div>

            {/* Docs content */}
            <div className="lg:col-span-3 max-w-4xl space-y-16">
              
              {/* Header */}
              <div className="border-b border-border/30 pb-8">
                <h1 className="text-4xl font-extrabold tracking-tight mb-4 lg:text-5xl bg-gradient-to-r from-foreground via-foreground/90 to-muted-foreground bg-clip-text text-transparent">
                  Documentation
                </h1>
                <p className="text-lg sm:text-xl text-muted-foreground max-w-3xl leading-relaxed">
                  Welcome to the Autonomous Software Engineering Platform (ASEP) manuals. Learn how to securely scale local agent groups with structural guarantees.
                </p>
              </div>

              {/* Sections */}
              <div className="space-y-24">
                
                {/* 1. Overview */}
                <section id="overview" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Book className="h-7 w-7 text-primary" />
                    Overview
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      ASEP provides developers and security teams with an isolated control plane to host autonomous software agents. Unlike standard cloud-based coding assistants, ASEP coordinates agents directly inside secure, local runtime sandboxes on your workspace host, connecting with standard Git and IDE toolchains under enterprise governance controls.
                    </p>
                    <p className="text-muted-foreground leading-relaxed">
                      By prioritizing local infrastructure execution, ASEP avoids public code storage leaks while maintaining full compliance protocols. We bridge the gap between autonomous performance and security constraints.
                    </p>
                  </div>
                </section>

                {/* 2. Installation */}
                <section id="installation" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Code className="h-7 w-7 text-primary" />
                    Installation
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      The platform runtime executes in Docker containers, managing distinct services for memory logging (Redis), code semantic indexing (Qdrant), structure relation (Postgres), and API servers.
                    </p>
                    <h3 className="text-lg font-semibold mt-4">System Requirements</h3>
                    <ul className="list-disc list-inside text-muted-foreground space-y-2">
                      <li>Docker & Docker Compose (v2.0 or higher)</li>
                      <li>Node.js (v18.0 or higher)</li>
                      <li>Python (v3.10 or higher)</li>
                    </ul>
                    <h3 className="text-lg font-semibold mt-4">Quick Setup</h3>
                    <div className="bg-muted p-4 rounded-lg font-mono text-xs overflow-x-auto border border-border/50">
                      git clone https://github.com/rounakkumarsah/ASEP.git<br/>
                      cd ASEP<br/>
                      docker compose up --build -d
                    </div>
                  </div>
                </section>

                {/* 3. Quickstart Guide */}
                <section id="quickstart" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Layers className="h-7 w-7 text-primary" />
                    Quickstart Guide
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      Follow these steps to get your first workspace up and running and register an agent executor:
                    </p>
                    <ol className="list-decimal list-inside text-muted-foreground space-y-2">
                      <li>Launch the stack via Docker Compose.</li>
                      <li>Navigate to the frontend at <code className="text-xs bg-muted px-1.5 py-0.5 rounded">http://localhost:3000</code>.</li>
                      <li>Go to <Link href="/signup" className="text-primary hover:underline">/signup</Link> to create your initial administrator account.</li>
                      <li>Verify your email using the local SMTP testing inbox.</li>
                      <li>Configure your first workspace path using absolute host directory paths.</li>
                    </ol>
                  </div>
                </section>

                {/* 4. Agent Topology */}
                <section id="topology" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Cpu className="h-7 w-7 text-primary" />
                    Agent Topology
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      ASEP uses a multi-tier agent layout where specialized roles coordinate to complete software tasks:
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-6">
                      <div className="p-5 border border-border/40 rounded-xl bg-card/30">
                        <h4 className="font-semibold text-foreground mb-2">Planner</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">Analyzes codebase files and constructs a linear step-by-step implementation artifact.</p>
                      </div>
                      <div className="p-5 border border-border/40 rounded-xl bg-card/30">
                        <h4 className="font-semibold text-foreground mb-2">Executor</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">Applies atomic file modifications and executes compiler commands within the sandbox environment.</p>
                      </div>
                      <div className="p-5 border border-border/40 rounded-xl bg-card/30">
                        <h4 className="font-semibold text-foreground mb-2">Reviewer</h4>
                        <p className="text-xs text-muted-foreground leading-relaxed">Runs lint checkers, verification scripts, and test suites to prevent regression.</p>
                      </div>
                    </div>
                  </div>
                </section>

                {/* 5. Sandbox Security */}
                <section id="security" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Shield className="h-7 w-7 text-primary" />
                    Sandbox Security
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      Prevent AI hallucinations from deleting resources or rewriting master branches. The built-in HITL checkpoint gate suspends executor agents when high-risk operations (e.g. force push, server shutdown) are initiated, dispatching real-time browser confirmations.
                    </p>
                    <p className="text-muted-foreground leading-relaxed">
                      All executing processes are confined to temporary docker instances with limited host filesystem access, strictly respecting rules defined in configuration.
                    </p>
                  </div>
                </section>

                {/* 6. Memory Synchronization */}
                <section id="memory" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Database className="h-7 w-7 text-primary" />
                    Memory Synchronization
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      To keep agents aligned with massive code changes, ASEP syncs memory files using:
                    </p>
                    <ul className="list-disc list-inside text-muted-foreground space-y-2">
                      <li><strong>Relational mapping:</strong> PostgreSQL for schema configuration and task execution tracking.</li>
                      <li><strong>Semantic Cache:</strong> Redis caching layers for quick command evaluation and rate limiting.</li>
                      <li><strong>Vector database:</strong> Qdrant vector database for semantic chunk retrieval.</li>
                    </ul>
                  </div>
                </section>

                {/* 7. Authentication */}
                <section id="authentication" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Key className="h-7 w-7 text-primary" />
                    Authentication
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      The platform enforces secure access with:
                    </p>
                    <ul className="list-disc list-inside text-muted-foreground space-y-2">
                      <li><strong>Argon2id:</strong> Password hashing to prevent brute force attacks.</li>
                      <li><strong>Cloudflare Turnstile:</strong> Integrated human verification for signup endpoints.</li>
                      <li><strong>HttpOnly Cookies:</strong> JWT access and refresh tokens are stored in secure cookies, isolating them from JavaScript execution.</li>
                    </ul>
                  </div>
                </section>

                {/* 8. Workspace Control */}
                <section id="workspace" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <FolderGit className="h-7 w-7 text-primary" />
                    Workspace Control
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      The API endpoint <code className="text-xs bg-muted px-1.5 py-0.5 rounded">/api/v1/workspace</code> exposes direct management over absolute workspace mounts. This allows programmatic workspace creation, mapping of local host repositories, and isolated sandbox generation.
                    </p>
                  </div>
                </section>

                {/* 9. Governance Webhooks */}
                <section id="webhooks" className="scroll-mt-36">
                  <h2 className="text-3xl font-bold mb-6 flex items-center gap-3 border-b border-border/20 pb-2">
                    <Workflow className="h-7 w-7 text-primary" />
                    Governance Webhooks
                  </h2>
                  <div className="prose prose-invert max-w-none space-y-4">
                    <p className="text-muted-foreground leading-relaxed">
                      Configure custom webhooks under Settings to forward system audit events to third-party endpoints. Common webhook payloads contain actor definitions, audit severities, action types, and response validation results.
                    </p>
                  </div>
                </section>

              </div>
            </div>
            
          </div>
        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
