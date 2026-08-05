"use client";

import * as React from "react";
import Link from "next/link";
import { LandingNavbar } from "@/components/landing/navbar";
import { LandingFooter } from "@/components/landing/footer";
import { 
  CheckCircle2, 
  Clock, 
  Calendar, 
  Layers,
  ChevronDown,
  ChevronUp,
  Search,
  Filter
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Milestone {
  title: string;
  category: "AI Agents" | "Governance" | "Security" | "MCP" | "RAG" | "Multi-tenant" | "Billing" | "SSO" | "Audit" | "Analytics" | "API" | "Mobile" | "Infrastructure";
  status: "completed" | "in-progress" | "planned" | "research";
  priority: "High" | "Medium" | "Low";
  eta: string;
  dependencies: string[];
  businessValue: string;
  technicalNotes: string;
}

export default function RoadmapPage() {
  const [searchTerm, setSearchTerm] = React.useState("");
  const [selectedCategory, setSelectedCategory] = React.useState<string>("all");
  const [selectedStatus, setSelectedStatus] = React.useState<string>("all");
  const [expandedItems, setExpandedItems] = React.useState<Record<string, boolean>>({});

  const toggleExpand = (title: string) => {
    setExpandedItems(prev => ({ ...prev, [title]: !prev[title] }));
  };

  const milestones: Milestone[] = [
    // Completed
    {
      title: "Async PostgreSQL Storage Pool",
      category: "Infrastructure",
      status: "completed",
      priority: "High",
      eta: "Q2 2026",
      dependencies: ["Docker relational container base"],
      businessValue: "Provides high-performance, scoped ORM mapping transactions to track execution runs safely.",
      technicalNotes: "Uses SQLAlchemy 2.0 and asyncpg connection pooling under FastAPI lifecycle lifespan events.",
    },
    {
      title: "Local Semantic Vector Cache",
      category: "RAG",
      status: "completed",
      priority: "High",
      eta: "Q2 2026",
      dependencies: ["Qdrant docker container mapping"],
      businessValue: "Allows agents to search massive codebases locally and retrieve relevant chunks in milliseconds.",
      technicalNotes: "Integrates Qdrant client, absolute workspace directory mapping, and local embeddings pipelines.",
    },
    {
      title: "Human-in-the-Loop Intercept Gates",
      category: "Governance",
      status: "completed",
      priority: "High",
      eta: "Q2 2026",
      dependencies: ["Relational tracking schemas"],
      businessValue: "Prevents autonomous agents from modifying critical branches or launching high-risk commands without approval.",
      technicalNotes: "Built a checkpoint interceptor that prompts for confirmations inside the platform dashboard.",
    },
    {
      title: "Model Context Protocol (MCP) Interface",
      category: "MCP",
      status: "completed",
      priority: "High",
      eta: "Q2 2026",
      dependencies: ["Agent execution runtime"],
      businessValue: "Allows agents to securely interface with compilers, code execution sandboxes, and file systems.",
      technicalNotes: "Integrated explicit script rendering and validation rules via the standardized MCP protocol.",
    },
    // In Progress
    {
      title: "Enterprise SAML SSO Integrations",
      category: "SSO",
      status: "in-progress",
      priority: "High",
      eta: "Q3 2026",
      dependencies: ["Authentication security layer"],
      businessValue: "Allows IT departments to coordinate identity provisioning through Okta, Azure AD, and Ping Identity.",
      technicalNotes: "Implements XML assertions verification, metadata sync endpoints, and token mapping handlers.",
    },
    {
      title: "Namespace Role-Based Permissions (RBAC)",
      category: "Security",
      status: "in-progress",
      priority: "High",
      eta: "Q3 2026",
      dependencies: ["User storage schema"],
      businessValue: "Restricts autonomous agent processes to specific directories, restricting file system modifications.",
      technicalNotes: "Utilizes permission policies loaded in the FastAPI route layers and directory sandbox checks.",
    },
    {
      title: "Workspace Resource Usage Telemetry",
      category: "Analytics",
      status: "in-progress",
      priority: "Medium",
      eta: "Q4 2026",
      dependencies: ["Docker runtime client"],
      businessValue: "Gives administrators visibility into CPU, memory, and LLM token usage details per agent session.",
      technicalNotes: "Implements real-time resource polling inside the execution thread and forwards events to Qdrant/Postgres.",
    },
    // Planned
    {
      title: "Stripe Billing & Subscription Engine",
      category: "Billing",
      status: "planned",
      priority: "Medium",
      eta: "Q4 2026",
      dependencies: ["Workspace control API"],
      businessValue: "Supports tiered billing subscriptions, payment gateway integrations, and automatic invoicing.",
      technicalNotes: "Registers webhooks to sync billing status attributes with user accounts inside PostgreSQL database.",
    },
    {
      title: "Cryptographic Multi-Tenant Boundaries",
      category: "Multi-tenant",
      status: "planned",
      priority: "High",
      eta: "Q1 2027",
      dependencies: ["Security RBAC layer"],
      businessValue: "Guarantees absolute workspace isolation for multiple developers running tasks on a single host.",
      technicalNotes: "Enforces kernel-level container isolates and workspace mount encryptions.",
    },
    {
      title: "API Keys Provisioning Dashboard",
      category: "API",
      status: "planned",
      priority: "Medium",
      eta: "Q1 2027",
      dependencies: ["Authentication security layer"],
      businessValue: "Allows developers to generate custom API keys for triggering autonomous workflows externally.",
      technicalNotes: "Implements key rotation mechanisms, secret storage patterns, and authorization headers check.",
    },
    // Research
    {
      title: "Decentralized Evaluation Framework",
      category: "AI Agents",
      status: "research",
      priority: "Low",
      eta: "Q2 2027",
      dependencies: ["Telemetry loggers"],
      businessValue: "Automatically flags hallucination parameters and checks code accuracy metrics using multiple consensus models.",
      technicalNotes: "Researching async prompt verification networks and decentralized evaluator checkpoints.",
    },
    {
      title: "Companion Mobile Console Dashboard",
      category: "Mobile",
      status: "research",
      priority: "Low",
      eta: "Q2 2027",
      dependencies: ["API Key framework"],
      businessValue: "Allows administrators to approve Human-in-the-Loop checkpoints on the go via mobile notifications.",
      technicalNotes: "Investigating React Native web bridges and push notification token registries.",
    },
  ];

  // Categories list
  const categories = ["all", "AI Agents", "Governance", "Security", "MCP", "RAG", "Multi-tenant", "Billing", "SSO", "Audit", "Analytics", "API", "Mobile", "Infrastructure"];

  // Filter logic
  const filteredMilestones = milestones.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          item.technicalNotes.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "all" || item.category === selectedCategory;
    const matchesStatus = selectedStatus === "all" || item.status === selectedStatus;
    return matchesSearch && matchesCategory && matchesStatus;
  });

  // JSON-LD Structured Data
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "ProductRoadmap",
    "name": "ASEP Platform Roadmap",
    "description": "Quarterly engineering milestones and product features plan for the Autonomous Software Engineering Platform.",
    "publisher": {
      "@type": "Organization",
      "name": "ASEP",
      "logo": {
        "@type": "ImageObject",
        "url": "https://asep.local/logo.png"
      }
    }
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
            <span className="text-foreground font-medium">Roadmap</span>
          </nav>

          {/* Hero */}
          <div className="border-b border-border/30 pb-8 mb-12">
            <h1 className="text-4xl font-extrabold tracking-tight mb-4 lg:text-5xl bg-gradient-to-r from-foreground via-foreground/90 to-muted-foreground bg-clip-text text-transparent">
              Enterprise Product Roadmap
            </h1>
            <p className="text-lg sm:text-xl text-muted-foreground max-w-3xl leading-relaxed">
              Understand our security vision, check quarterly progress windows, and analyze the technical layout backing the ASEP workspace control plane.
            </p>
          </div>

          {/* Search & Filters */}
          <div className="p-6 border border-border/40 rounded-xl bg-card/30 backdrop-blur-sm mb-8 space-y-4">
            <div className="flex flex-col md:flex-row gap-4 items-center">
              <div className="relative w-full md:flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search roadmap items..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full text-sm pl-9 pr-4 py-2 rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-muted-foreground/60"
                />
              </div>

              {/* Status Filter */}
              <div className="flex items-center gap-2 w-full md:w-auto">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full md:w-44 text-sm py-2 px-3 rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="all">All Statuses</option>
                  <option value="completed">Completed</option>
                  <option value="in-progress">In Progress</option>
                  <option value="planned">Planned</option>
                  <option value="research">Under Research</option>
                </select>
              </div>

              {/* Category Filter */}
              <div className="flex items-center gap-2 w-full md:w-auto">
                <Layers className="h-4 w-4 text-muted-foreground" />
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full md:w-48 text-sm py-2 px-3 rounded-lg border border-border/60 bg-background/50 focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="all">All Tracks</option>
                  {categories.filter(c => c !== "all").map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Timeline & Cards Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
            
            {/* Timeline sidebar indicator */}
            <div className="hidden lg:block lg:col-span-1">
              <div className="sticky top-32 border-l border-border/30 pl-4 py-2 space-y-4">
                <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Release Timeline</h3>
                <div className="flex flex-col gap-2 text-sm">
                  <div className="flex items-center gap-2 font-semibold text-primary">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    <span>Q2 2026 (Live)</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Clock className="h-4 w-4 text-primary animate-pulse" />
                    <span>Q3 2026 (Active)</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>Q4 2026 (Planned)</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>Q1 2027 (Planned)</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Layers className="h-4 w-4" />
                    <span>Q2 2027 (Research)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Milestones Content List */}
            <div className="lg:col-span-3 space-y-6">
              <AnimatePresence mode="popLayout">
                {filteredMilestones.map((item) => {
                  const isExpanded = !!expandedItems[item.title];
                  return (
                    <motion.div
                      layout
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ duration: 0.25 }}
                      key={item.title}
                      className="border border-border/40 rounded-xl bg-card/30 backdrop-blur-sm hover:border-border/60 transition-all overflow-hidden shadow-sm"
                    >
                      {/* Accordion Trigger */}
                      <button
                        onClick={() => toggleExpand(item.title)}
                        className="w-full text-left p-6 flex items-start justify-between gap-4 outline-none focus-visible:bg-muted/30"
                      >
                        <div className="space-y-1.5 min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted/70 text-muted-foreground border border-border/20">
                              {item.category}
                            </span>
                            <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                              item.status === "completed" ? "bg-green-500/10 text-green-500" :
                              item.status === "in-progress" ? "bg-primary/10 text-primary animate-pulse" :
                              item.status === "planned" ? "bg-[#38BDF8]/10 text-[#38BDF8]" : "bg-[#22D3EE]/10 text-[#22D3EE]"
                            }`}>
                              {item.status.toUpperCase().replace("-", " ")}
                            </span>
                            <span className={`text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded ${
                              item.priority === "High" ? "bg-red-500/10 text-red-500" :
                              item.priority === "Medium" ? "bg-yellow-500/10 text-yellow-500" : "bg-blue-500/10 text-blue-500"
                            }`}>
                              {item.priority} Priority
                            </span>
                          </div>
                          <h3 className="text-lg font-bold text-foreground">{item.title}</h3>
                          <p className="text-xs text-muted-foreground">Target Release Window: {item.eta}</p>
                        </div>
                        {isExpanded ? <ChevronUp className="h-5 w-5 text-muted-foreground mt-1" /> : <ChevronDown className="h-5 w-5 text-muted-foreground mt-1" />}
                      </button>

                      {/* Expandable Content Area */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0 }}
                            animate={{ height: "auto" }}
                            exit={{ height: 0 }}
                            className="overflow-hidden border-t border-border/20 bg-muted/10"
                          >
                            <div className="p-6 space-y-4 text-sm leading-relaxed">
                              {item.dependencies && item.dependencies.length > 0 && (
                                <div>
                                  <h4 className="text-xs font-bold text-muted-foreground uppercase mb-1">Dependencies</h4>
                                  <div className="flex flex-wrap gap-1">
                                    {item.dependencies.map(d => (
                                      <span key={d} className="text-xs font-medium bg-muted border border-border/50 px-2 py-0.5 rounded">{d}</span>
                                    ))}
                                  </div>
                                </div>
                              )}
                              <div>
                                <h4 className="text-xs font-bold text-muted-foreground uppercase mb-1">Business Value</h4>
                                <p className="text-muted-foreground text-xs">{item.businessValue}</p>
                              </div>
                              <div>
                                <h4 className="text-xs font-bold text-muted-foreground uppercase mb-1">Technical Implementation</h4>
                                <p className="text-muted-foreground text-xs font-mono bg-card/60 p-3 rounded border border-border/30 overflow-x-auto">{item.technicalNotes}</p>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>

                    </motion.div>
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
