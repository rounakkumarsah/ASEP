"use client";

import * as React from "react";
import Link from "next/link";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { 
  GitCommit, 
  Search, 
  Copy, 
  Check, 
  ExternalLink,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ReleaseItem {
  version: string;
  date: string;
  type: "Major Feature" | "Minor Update" | "Security Release" | "Beta Launch";
  commitHash: string;
  summary: string;
  details: {
    new?: string[];
    improved?: string[];
    fixed?: string[];
    security?: string[];
  };
  migrationNotes?: string;
  knownIssues?: string[];
}

export default function ChangelogPage() {
  const [searchTerm, setSearchTerm] = React.useState("");
  const [selectedType, setSelectedType] = React.useState<"all" | "new" | "improved" | "fixed" | "security">("all");
  const [copiedText, setCopiedText] = React.useState<string | null>(null);
  const [expandedReleases, setExpandedReleases] = React.useState<Record<string, boolean>>({});

  const handleCopy = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(`${type}-${text}`);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const toggleExpand = (version: string) => {
    setExpandedReleases(prev => ({ ...prev, [version]: !prev[version] }));
  };

  const releases: ReleaseItem[] = [
    {
      version: "v0.5.0",
      date: "July 20, 2026",
      type: "Security Release",
      commitHash: "0856574",
      summary: "Production authentication hardening, Cloudflare Turnstile explicit rendering, and Navigation route audits.",
      details: {
        new: [
          "Created dedicated subpages for Roadmap, Changelog, and API documentation.",
          "Added floating ThemeToggle to a shared AuthLayout structure.",
          "Implemented table-of-contents scroll spy using IntersectionObserver for general documentation.",
        ],
        improved: [
          "Upgraded password requirements schema: minimum 12 characters, uppercase, lowercase, numbers, and symbols.",
          "Harden cookie configuration rules: JWT access/refresh tokens are now saved in isolated secure HttpOnly Lax cookies.",
        ],
        fixed: [
          "Resolved routing redirect loops on general documentation sidebar elements and footers.",
          "Fixed typescript compilation warnings and ESLint unused-import exceptions.",
        ],
        security: [
          "Removed all JWT and secret tokens from localStorage/sessionStorage.",
          "Strict cookie attributes: Secure=true, HttpOnly=true, SameSite=Lax, Path=/.",
        ],
      },
      migrationNotes: "Ensure all client clients support secure cookie storage. Local storage of tokens is no longer permitted.",
      knownIssues: [
        "Cloudflare Turnstile token validation may return timeout-or-duplicate if reused within the 5-minute timeout window.",
      ],
    },
    {
      version: "v0.4.8",
      date: "July 15, 2026",
      type: "Minor Update",
      commitHash: "14a7a58",
      summary: "Phase 4.8 — Knowledge Synchronization Engine. Relational mapping database integration.",
      details: {
        new: [
          "Added file status change detection and incremental workspace indexing.",
          "Added directory crawler tools for scanning workspace volumes locally.",
        ],
        improved: [
          "Enhanced Qdrant vector embedding chunking logic.",
        ],
      },
    },
    {
      version: "v0.4.7",
      date: "July 5, 2026",
      type: "Minor Update",
      commitHash: "493264b",
      summary: "Phase 4.7 — Enterprise Evaluation Framework and hallucination trackers.",
      details: {
        new: [
          "Built diagnostics test suites to check LLM validation accuracies.",
        ],
      },
    },
    {
      version: "v0.4.6",
      date: "June 25, 2026",
      type: "Major Feature",
      commitHash: "a8b667f",
      summary: "Phase 4.6 — Autonomous Workflow Engine. Implementation of state machines.",
      details: {
        new: [
          "Integrated LangGraph workflow runners for coordinating Supervisor/Executor agent handoffs.",
        ],
      },
    },
    {
      version: "v0.4.5",
      date: "June 15, 2026",
      type: "Major Feature",
      commitHash: "41fe8ef",
      summary: "Phase 4.5 — Human-in-the-Loop Intercept Gates.",
      details: {
        new: [
          "Created control plane validation intercept checkpoints for high-risk terminal commands.",
        ],
      },
    },
    {
      version: "v0.4.0",
      date: "June 1, 2026",
      type: "Major Feature",
      commitHash: "85111f8",
      summary: "Phase 4.4 — MCP Tool Ecosystem and GovernanceAgent Policy gating.",
      details: {
        new: [
          "Integrated Model Context Protocol (MCP) clients inside execution sandboxes.",
          "Implemented GovernanceAgent verification rules on filesystem queries.",
        ],
      },
    },
    {
      version: "v0.1.0",
      date: "May 1, 2026",
      type: "Beta Launch",
      commitHash: "347aabc",
      summary: "Initial Beta Relational Storage & Core Control Plane.",
      details: {
        new: [
          "Configured async PostgreSQL pooling using SQLAlchemy 2.0 and asyncpg.",
          "Added readiness and healthcheck probes for FastAPI lifecycle management.",
        ],
      },
    },
  ];

  // Filter logic
  const filteredReleases = releases.filter(release => {
    const matchesSearch = 
      release.version.toLowerCase().includes(searchTerm.toLowerCase()) ||
      release.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      release.type.toLowerCase().includes(searchTerm.toLowerCase());

    if (!matchesSearch) return false;
    if (selectedType === "all") return true;

    return !!release.details[selectedType]?.length;
  });

  // JSON-LD Structured Data
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "ASEP Changelog",
    "description": "Historical releases and technical updates log for the Autonomous Software Engineering Platform (ASEP).",
    "codeRepository": "https://github.com/rounakkumarsah/ASEP",
    "programmingLanguage": "TypeScript, Python",
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Structured SEO Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <LandingNavbar />

      <main className="flex-1 pt-32 pb-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          
          {/* Breadcrumbs */}
          <nav className="mb-8 flex items-center space-x-2 text-sm text-muted-foreground" aria-label="Breadcrumb">
            <Link href="/" className="hover:text-foreground transition-colors">Home</Link>
            <span>/</span>
            <span className="text-foreground font-medium">Changelog</span>
          </nav>

          {/* Header Section */}
          <div className="border-b border-border/30 pb-8 mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h1 className="text-4xl font-extrabold tracking-tight mb-4 lg:text-5xl bg-gradient-to-r from-foreground via-foreground/90 to-muted-foreground bg-clip-text text-transparent">
                System Changelog
              </h1>
              <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl leading-relaxed">
                Stay updated with release notes, security upgrades, and actual repository commit hashes.
              </p>
            </div>
            
            {/* Search Input */}
            <div className="relative w-full md:w-80">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search versions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full text-sm pl-9 pr-4 py-2 rounded-lg border border-border/60 bg-card/50 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-muted-foreground/60"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
            {/* Left Filter Options */}
            <div className="lg:col-span-1">
              <div className="sticky top-32 space-y-6">
                <div>
                  <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase mb-3 px-2">
                    Filter by Changes
                  </h3>
                  <div className="flex flex-col gap-1">
                    {[
                      { id: "all", label: "All Updates" },
                      { id: "new", label: "New Features" },
                      { id: "improved", label: "Improvements" },
                      { id: "fixed", label: "Bug Fixes" },
                      { id: "security", label: "Security Hardening" },
                    ].map(filter => (
                      <button
                        key={filter.id}
                        onClick={() => setSelectedType(filter.id as typeof selectedType)}
                        className={`text-left px-3 py-2 rounded-lg text-sm transition-all outline-none focus-visible:ring-2 focus-visible:ring-primary ${
                          selectedType === filter.id
                            ? "bg-primary/10 text-primary font-semibold"
                            : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                        }`}
                      >
                        {filter.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="p-4 border border-border/40 rounded-xl bg-card/40 backdrop-blur-sm text-xs text-muted-foreground leading-relaxed">
                  <p className="font-semibold text-foreground mb-1.5 flex items-center gap-1.5">
                    <GitCommit className="h-4 w-4 text-primary" />
                    Commit History
                  </p>
                  Each change tag below corresponds directly to a verified commit on the master repository. Use the copy commands to reference hashes.
                </div>
              </div>
            </div>

            {/* Changelog Timeline Card Grid */}
            <div className="lg:col-span-3 space-y-8">
              <AnimatePresence mode="popLayout">
                {filteredReleases.map(release => {
                  const isExpanded = !!expandedReleases[release.version];
                  const copyVersionId = `version-${release.version}`;
                  const copyCommitId = `commit-${release.commitHash}`;
                  
                  return (
                    <motion.article
                      layout
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ duration: 0.25 }}
                      key={release.version}
                      className="p-6 md:p-8 border border-border/40 rounded-xl bg-card/30 backdrop-blur-sm space-y-6"
                    >
                      {/* Version Card Header */}
                      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border/20 pb-4">
                        <div className="flex items-center gap-3">
                          <h2 className="text-2xl font-extrabold tracking-tight text-foreground">{release.version}</h2>
                          
                          {/* Copy Version Tag */}
                          <button
                            onClick={() => handleCopy(release.version, "version")}
                            className="p-1 rounded hover:bg-muted/50 text-muted-foreground transition-all"
                            title="Copy version tag"
                          >
                            {copiedText === copyVersionId ? <span className="text-[10px] text-green-500 font-semibold">Copied!</span> : <Copy className="h-3.5 w-3.5" />}
                          </button>

                          <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-primary/10 text-primary border border-primary/20">
                            {release.type}
                          </span>
                        </div>

                        {/* Commit Copy Action */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleCopy(release.commitHash, "commit")}
                            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary transition-colors font-mono bg-muted/60 border border-border/40 px-2.5 py-1 rounded"
                            title="Copy commit hash"
                          >
                            <GitCommit className="h-3.5 w-3.5" />
                            <span>{release.commitHash}</span>
                            {copiedText === copyCommitId ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                          </button>
                          
                          <Link
                            href={`https://github.com/rounakkumarsah/ASEP/commit/${release.commitHash}`}
                            target="_blank"
                            className="p-1.5 rounded bg-muted/60 border border-border/40 text-muted-foreground hover:text-primary transition-all"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                          </Link>
                        </div>
                      </div>

                      {/* Content summary */}
                      <div className="space-y-4">
                        <p className="text-sm text-foreground leading-relaxed">{release.summary}</p>
                        
                        {/* Categories items list */}
                        <div className="space-y-4">
                          {release.details.new && release.details.new.length > 0 && (
                            <div>
                              <h4 className="text-xs font-bold uppercase tracking-wider text-green-500 mb-2">New</h4>
                              <ul className="space-y-1.5 text-xs text-muted-foreground list-disc list-inside">
                                {release.details.new.map((c, i) => <li key={i}>{c}</li>)}
                              </ul>
                            </div>
                          )}

                          {release.details.improved && release.details.improved.length > 0 && (
                            <div>
                              <h4 className="text-xs font-bold uppercase tracking-wider text-blue-500 mb-2">Improved</h4>
                              <ul className="space-y-1.5 text-xs text-muted-foreground list-disc list-inside">
                                {release.details.improved.map((c, i) => <li key={i}>{c}</li>)}
                              </ul>
                            </div>
                          )}

                          {release.details.fixed && release.details.fixed.length > 0 && (
                            <div>
                              <h4 className="text-xs font-bold uppercase tracking-wider text-yellow-500 mb-2">Fixed</h4>
                              <ul className="space-y-1.5 text-xs text-muted-foreground list-disc list-inside">
                                {release.details.fixed.map((c, i) => <li key={i}>{c}</li>)}
                              </ul>
                            </div>
                          )}

                          {release.details.security && release.details.security.length > 0 && (
                            <div>
                              <h4 className="text-xs font-bold uppercase tracking-wider text-red-500 mb-2">Security</h4>
                              <ul className="space-y-1.5 text-xs text-muted-foreground list-disc list-inside">
                                {release.details.security.map((c, i) => <li key={i}>{c}</li>)}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Expandable Meta Notes Toggle */}
                      {(release.migrationNotes || release.knownIssues) && (
                        <div>
                          <button
                            onClick={() => toggleExpand(release.version)}
                            className="flex items-center gap-1.5 text-xs font-semibold text-primary hover:underline"
                          >
                            <span>{isExpanded ? "Hide Details" : "Show Migration & Known Issues"}</span>
                            {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          </button>

                          <AnimatePresence>
                            {isExpanded && (
                              <motion.div
                                initial={{ height: 0 }}
                                animate={{ height: "auto" }}
                                exit={{ height: 0 }}
                                className="overflow-hidden"
                              >
                                <div className="pt-4 grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                                  {release.migrationNotes && (
                                    <div className="p-4 rounded-lg bg-yellow-500/5 border border-yellow-500/10 space-y-1">
                                      <h5 className="text-xs font-bold text-yellow-600 dark:text-yellow-400 uppercase tracking-wide">Migration Notes</h5>
                                      <p className="text-xs text-muted-foreground leading-relaxed">{release.migrationNotes}</p>
                                    </div>
                                  )}
                                  {release.knownIssues && (
                                    <div className="p-4 rounded-lg bg-red-500/5 border border-red-500/10 space-y-1">
                                      <h5 className="text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wide">Known Issues</h5>
                                      <ul className="list-disc list-inside text-xs text-muted-foreground space-y-0.5">
                                        {release.knownIssues.map((issue, idx) => <li key={idx}>{issue}</li>)}
                                      </ul>
                                    </div>
                                  )}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      )}

                    </motion.article>
                  );
                })}
              </AnimatePresence>
            </div>
          </div>

        </div>
      </main>

      <LandingFooter />
    </div>
  );
}
