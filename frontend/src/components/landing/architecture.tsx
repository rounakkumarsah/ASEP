"use client";

import React, { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import {
  User,
  BrainCircuit,
  Terminal,
  Database,
  Wrench,
  ShieldCheck,
  LayoutDashboard,
  CheckCircle,
  ArrowRight,
  Info,
} from "lucide-react";
import { AnimatedBeam } from "@/components/ui/animated-beam";
import { Button } from "@/components/ui/button";

type NodeDetails = {
  title: string;
  subtitle: string;
  description: string;
  role: string;
  tech: string;
};

const NODES_DATA: Record<string, NodeDetails> = {
  user: {
    title: "User Input Trigger",
    subtitle: "Orchestration request entry point",
    description: "The developer defines the primary goal (e.g., 'Fix memory leak' or 'Build authentication provider'). The request enters the secure runtime environment.",
    role: "User / CI-CD pipeline webhook",
    tech: "FastAPI REST API",
  },
  planner: {
    title: "Deconstruction Planner",
    subtitle: "AI Reasoning & Decomposition",
    description: "Generates a deterministic DAG (Directed Acyclic Graph) of subtasks, identifying dependencies and planning execution routes ahead of time.",
    role: "Target decomposition, dependency mapping",
    tech: "LangGraph / LLM Execution Planning",
  },
  executor: {
    title: "Isolated Sandbox Executor",
    subtitle: "Secure Code Execution",
    description: "Runs code, compiles files, and runs verification suites inside decoupled Docker container workspaces with CPU/Memory limits.",
    role: "Decoupled task execution & sandbox compilation",
    tech: "Docker Engine / Python Runtime API",
  },
  governance: {
    title: "Governance Guard",
    subtitle: "Strict Policy Enforcement",
    description: "Enforces strict human-in-the-loop validation checkpoints and signs cryptographically approved actions before execution.",
    role: "HITL approvals, cryptographic policy gates",
    tech: "Cryptographic signatures, webhook hooks",
  },
  memory: {
    title: "Multi-Layer Memory Engine",
    subtitle: "Graph Context & RAG storage",
    description: "Maintains 3 distinct layers: working memory, vector RAG embeddings in Qdrant, and persistent architectural knowledge graphs in Neo4j.",
    role: "Context retrieval & semantic persistence",
    tech: "Qdrant (Vector) & Neo4j (Graph DB)",
  },
  controlPlane: {
    title: "Control Plane Orchestrator",
    subtitle: "State Machine & Telemetry Hub",
    description: "Coordinates state transitions across all subagents, monitors performance metrics, and dynamically handles failure recoveries in real time.",
    role: "Central event loop & cluster telemetry",
    tech: "Redis Streams / PostgreSQL state machine",
  },
  evaluation: {
    title: "Continuous Evaluation",
    subtitle: "Automated Verification Guardrails",
    description: "Runs test suites, linters, security audits, and semantic quality scoring to ensure code correctness before merging.",
    role: "Real-time accuracy & safety validation",
    tech: "PyTest, ESLint, Semgrep & LLM Judges",
  },
  tools: {
    title: "MCP Tool Registry",
    subtitle: "Extensible Integration Layer",
    description: "Standardized protocol allowing agents to invoke Git operations, filesystem access, terminal commands, and third-party APIs.",
    role: "Dynamic agent tool exposure & execution",
    tech: "Model Context Protocol (MCP) v1.0",
  },
};

export function ArchitectureSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);
  const plannerRef = useRef<HTMLDivElement>(null);
  const executorRef = useRef<HTMLDivElement>(null);
  const governanceRef = useRef<HTMLDivElement>(null);
  const memoryRef = useRef<HTMLDivElement>(null);
  const controlPlaneRef = useRef<HTMLDivElement>(null);
  const evaluationRef = useRef<HTMLDivElement>(null);
  const toolsRef = useRef<HTMLDivElement>(null);

  const [activeNode, setActiveNode] = useState<keyof typeof NODES_DATA>("planner");

  const handleKeyDown = (key: keyof typeof NODES_DATA) => (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      setActiveNode(key);
    }
  };

  return (
    <section id="architecture" className="relative py-20 sm:py-28 md:py-32 bg-background dark:bg-[#090B0F] overflow-hidden border-b border-border transition-colors duration-300">
      {/* Glow Backdrops */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[#22D3EE]/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-14 sm:mb-16 space-y-3 sm:space-y-4">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            Interactive Agent Control Plane
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Click on any module to inspect how data, state traces, and cryptographic policy signatures flow through ASEP.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          
          {/* Left / Center: Interactive DAG diagram */}
          <div className="lg:col-span-8 flex flex-col justify-center items-center">
            <div 
              ref={containerRef}
              className="relative w-full h-[520px] sm:h-[560px] md:h-[580px] border border-border/80 dark:border-[#202833] bg-card/40 dark:bg-[#0D1117]/30 backdrop-blur-xl rounded-2xl p-4 sm:p-6 overflow-hidden flex flex-col justify-between shadow-sm"
            >
              {/* Background grid */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border)/0.3)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.3)_1px,transparent_1px)] bg-[size:2rem_2rem] opacity-30 pointer-events-none" />

              {/* Row 1: Governance & Approvals */}
              <div className="flex justify-center w-full">
                <div 
                  ref={governanceRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("governance")}
                  onKeyDown={handleKeyDown("governance")}
                  className={`z-20 flex flex-col items-center justify-center p-3 rounded-xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "governance"
                      ? "bg-[#2DD4A3]/10 border-[#2DD4A3] text-[#2DD4A3] shadow-[0_0_15px_rgba(45,212,163,0.25)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-[#2DD4A3]/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect Governance Node"
                >
                  <ShieldCheck className="h-5 w-5 sm:h-6 sm:w-6 mb-1" />
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase">Governance</span>
                </div>
              </div>

              {/* Row 2: User -> Planner -> Control Plane -> Evaluation */}
              <div className="flex items-center justify-between w-full px-1 sm:px-6">
                
                {/* User Node */}
                <div 
                  ref={userRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("user")}
                  onKeyDown={handleKeyDown("user")}
                  className={`z-20 flex flex-col items-center justify-center p-2.5 sm:p-3 rounded-xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "user"
                      ? "bg-sky-500/10 border-[#22D3EE] text-[#22D3EE] shadow-[0_0_15px_rgba(34,211,238,0.25)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-[#22D3EE]/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect User Request Node"
                >
                  <User className="h-5 w-5 sm:h-6 sm:w-6 mb-1" />
                  <span className="text-[9px] sm:text-[10px] font-mono font-bold tracking-wider uppercase">User Request</span>
                </div>

                {/* Planner Node */}
                <div 
                  ref={plannerRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("planner")}
                  onKeyDown={handleKeyDown("planner")}
                  className={`z-20 flex flex-col items-center justify-center p-3 sm:p-4 rounded-2xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "planner"
                      ? "bg-[#22D3EE]/10 border-[#22D3EE] text-[#22D3EE] shadow-[0_0_20px_rgba(34,211,238,0.3)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-[#22D3EE]/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect AI Planner Node"
                >
                  <BrainCircuit className="h-6 w-6 sm:h-8 sm:w-8 mb-1" />
                  <span className="text-[10px] sm:text-xs font-mono font-bold tracking-wider uppercase">AI Planner</span>
                </div>

                {/* Control Plane Node */}
                <div 
                  ref={controlPlaneRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("controlPlane")}
                  onKeyDown={handleKeyDown("controlPlane")}
                  className={`z-20 flex flex-col items-center justify-center p-3 sm:p-4 rounded-2xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "controlPlane"
                      ? "bg-[#22D3EE]/10 border-[#22D3EE] text-[#22D3EE] shadow-[0_0_20px_rgba(34,211,238,0.3)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-[#22D3EE]/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect Control Plane Node"
                >
                  <LayoutDashboard className="h-6 w-6 sm:h-8 sm:w-8 mb-1" />
                  <span className="text-[10px] sm:text-xs font-mono font-bold tracking-wider uppercase">Control Plane</span>
                </div>

                {/* Evaluation Node */}
                <div 
                  ref={evaluationRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("evaluation")}
                  onKeyDown={handleKeyDown("evaluation")}
                  className={`z-20 flex flex-col items-center justify-center p-2.5 sm:p-3 rounded-xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "evaluation"
                      ? "bg-indigo-500/10 border-indigo-400 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.25)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-indigo-400/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect Evaluation Node"
                >
                  <CheckCircle className="h-5 w-5 sm:h-6 sm:w-6 mb-1" />
                  <span className="text-[9px] sm:text-[10px] font-mono font-bold tracking-wider uppercase">Evaluation</span>
                </div>

              </div>

              {/* Row 3: Executor & Memory */}
              <div className="flex items-center justify-around w-full px-2 sm:px-6">
                
                {/* Executor Node */}
                <div 
                  ref={executorRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("executor")}
                  onKeyDown={handleKeyDown("executor")}
                  className={`z-20 flex flex-col items-center justify-center p-3 sm:p-3.5 rounded-xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "executor"
                      ? "bg-[#22D3EE]/10 border-[#22D3EE] text-[#22D3EE] shadow-[0_0_15px_rgba(34,211,238,0.25)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-[#22D3EE]/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect Docker Execution Sandbox Node"
                >
                  <Terminal className="h-5 w-5 sm:h-6 sm:w-6 mb-1" />
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase">Docker Exec</span>
                </div>

                {/* Memory Engine Node */}
                <div 
                  ref={memoryRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("memory")}
                  onKeyDown={handleKeyDown("memory")}
                  className={`z-20 flex flex-col items-center justify-center p-3 sm:p-3.5 rounded-xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "memory"
                      ? "bg-indigo-500/10 border-indigo-400 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.25)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-indigo-400/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect Memory Graph Node"
                >
                  <Database className="h-5 w-5 sm:h-6 sm:w-6 mb-1" />
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase">Memory Graph</span>
                </div>

              </div>

              {/* Row 4: Tools Registry */}
              <div className="flex justify-center w-full">
                <div 
                  ref={toolsRef}
                  role="button"
                  tabIndex={0}
                  onClick={() => setActiveNode("tools")}
                  onKeyDown={handleKeyDown("tools")}
                  className={`z-20 flex flex-col items-center justify-center p-3 rounded-xl border transition-all cursor-pointer min-h-[44px] focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none ${
                    activeNode === "tools"
                      ? "bg-amber-500/10 border-amber-400 text-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.25)]"
                      : "bg-card dark:bg-[#0D1117] border-border dark:border-[#202833] text-muted-foreground hover:border-amber-400/40 hover:text-foreground"
                  }`}
                  aria-label="Inspect MCP Tools Registry Node"
                >
                  <Wrench className="h-5 w-5 sm:h-6 sm:w-6 mb-1" />
                  <span className="text-[10px] font-mono font-bold tracking-wider uppercase">MCP Tools</span>
                </div>
              </div>

              {/* Animated Beams linking nodes */}
              <AnimatedBeam containerRef={containerRef} fromRef={userRef} toRef={plannerRef} gradientStartColor="#22D3EE" gradientStopColor="#22D3EE" duration={3.5} />
              <AnimatedBeam containerRef={containerRef} fromRef={plannerRef} toRef={governanceRef} curvature={-40} gradientStartColor="#22D3EE" gradientStopColor="#2DD4A3" duration={4} />
              <AnimatedBeam containerRef={containerRef} fromRef={governanceRef} toRef={plannerRef} reverse curvature={-40} gradientStartColor="#2DD4A3" gradientStopColor="#22D3EE" duration={4.2} />
              
              <AnimatedBeam containerRef={containerRef} fromRef={plannerRef} toRef={executorRef} curvature={40} gradientStartColor="#22D3EE" gradientStopColor="#22D3EE" duration={4.5} />
              <AnimatedBeam containerRef={containerRef} fromRef={executorRef} toRef={toolsRef} curvature={35} gradientStartColor="#22D3EE" gradientStopColor="#F59E0B" duration={3.8} />
              <AnimatedBeam containerRef={containerRef} fromRef={executorRef} toRef={memoryRef} gradientStartColor="#22D3EE" gradientStopColor="#6366F1" duration={5} />
              
              <AnimatedBeam containerRef={containerRef} fromRef={memoryRef} toRef={controlPlaneRef} gradientStartColor="#6366F1" gradientStopColor="#22D3EE" duration={4.8} />
              <AnimatedBeam containerRef={containerRef} fromRef={controlPlaneRef} toRef={evaluationRef} gradientStartColor="#22D3EE" gradientStopColor="#6366F1" duration={3.8} />
              
              {/* Feedback Loop Beams */}
              <AnimatedBeam containerRef={containerRef} fromRef={controlPlaneRef} toRef={plannerRef} reverse curvature={-50} gradientStartColor="#22D3EE" gradientStopColor="#22D3EE" duration={6} />
              <AnimatedBeam containerRef={containerRef} fromRef={evaluationRef} toRef={controlPlaneRef} reverse curvature={40} gradientStartColor="#6366F1" gradientStopColor="#22D3EE" duration={4.2} />

            </div>
          </div>

          {/* Right Column: Node Details Inspector Card */}
          <div className="lg:col-span-4 flex flex-col justify-between">
            <div className="border border-border/80 dark:border-[#202833] bg-card/80 dark:bg-[#0D1117]/60 backdrop-blur-md rounded-2xl p-5 sm:p-6 h-full flex flex-col justify-between space-y-6 shadow-sm">
              
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeNode}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-4 flex-1"
                >
                  <div className="flex items-center gap-2 text-primary font-mono text-xs uppercase tracking-widest font-bold">
                    <Info className="h-4 w-4" />
                    <span>Module Specification</span>
                  </div>

                  <div className="space-y-1">
                    <h3 className="text-xl font-extrabold text-foreground tracking-tight">
                      {NODES_DATA[activeNode].title}
                    </h3>
                    <p className="text-xs font-mono text-muted-foreground">
                      {NODES_DATA[activeNode].subtitle}
                    </p>
                  </div>

                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {NODES_DATA[activeNode].description}
                  </p>

                  <div className="pt-5 border-t border-border/80 dark:border-[#202833] space-y-3.5 text-xs font-mono">
                    <div>
                      <span className="text-muted-foreground block uppercase tracking-wider text-[10px]">Primary Role</span>
                      <span className="text-foreground font-semibold mt-1 block">{NODES_DATA[activeNode].role}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground block uppercase tracking-wider text-[10px]">Technology Stack</span>
                      <span className="text-foreground font-semibold mt-1 block">{NODES_DATA[activeNode].tech}</span>
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>

              {/* Bottom Quick-Action */}
              <div className="pt-4 border-t border-border/60 flex items-center justify-between">
                <span className="text-[10px] font-mono text-muted-foreground">CLICK NODES TO INSPECT</span>
                <Link href="/signup">
                  <Button size="sm" className="h-9 min-h-[36px] text-xs font-mono font-bold bg-[#22D3EE] hover:bg-[#67E8F9] text-[#090B0F] px-4 rounded-xl shadow-sm">
                    Launch
                    <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>

            </div>
          </div>

        </div>

      </div>
    </section>
  );
}
