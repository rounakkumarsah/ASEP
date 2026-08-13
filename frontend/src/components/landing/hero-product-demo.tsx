"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useMotionValue, useSpring, useTransform, AnimatePresence } from "framer-motion";
import {
  Terminal,
  Cpu,
  ShieldCheck,
  Database,
  Box,
  Lock,
  Workflow,
  Radio,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ── Agent Nodes in Pipeline ──────────────────────────────────────────────────
interface PipelineStep {
  id: string;
  name: string;
  role: string;
  status: "completed" | "active" | "queued";
  icon: React.ElementType;
  color: string;
  glow: string;
  time: string;
  meta: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "step-1",
    name: "DAG Planner",
    role: "Goal Deconstruction",
    status: "completed",
    icon: Workflow,
    color: "#38BDF8",
    glow: "rgba(56,189,248,0.4)",
    time: "0.42s",
    meta: "4 subtasks generated",
  },
  {
    id: "step-2",
    name: "Docker Sandbox",
    role: "Isolated Execution",
    status: "active",
    icon: Box,
    color: "#22D3EE",
    glow: "rgba(34,211,238,0.5)",
    time: "1.24s",
    meta: "npm run lint & test",
  },
  {
    id: "step-3",
    name: "3-Layer Memory",
    role: "Vector & Graph Sync",
    status: "active",
    icon: Database,
    color: "#2DD4A3",
    glow: "rgba(45,212,163,0.5)",
    time: "18ms",
    meta: "1,536d Qdrant embed",
  },
  {
    id: "step-4",
    name: "Governance Gate",
    role: "HITL Policy Validation",
    status: "queued",
    icon: ShieldCheck,
    color: "#F5B942",
    glow: "rgba(245,185,66,0.4)",
    time: "Pending",
    meta: "Signature verified",
  },
];

const STREAMING_LOGS = [
  { prefix: "[PLANNER]", msg: "Deconstructed goal 'Deploy Auth Microservice' into 4 tasks", col: "text-sky-400" },
  { prefix: "[SANDBOX]", msg: "Created isolated ephemeral workspace container #asep-248", col: "text-cyan-400" },
  { prefix: "[MCP-TOOL]", msg: "Mounted GitHub repository & Docker IPC socket via MCP v0.4", col: "text-emerald-400" },
  { prefix: "[EXECUTOR]", msg: "Running 'npm run lint' -> 0 warnings, 0 syntax errors", col: "text-teal-300" },
  { prefix: "[EXECUTOR]", msg: "Running 'npx tsc --noEmit' -> Strict type validation passed", col: "text-teal-300" },
  { prefix: "[MEMORY]", msg: "Retrieved 14 semantic chunks from Qdrant vector index", col: "text-cyan-300" },
  { prefix: "[GRAPH]", msg: "Committed execution DAG dependency edges to Neo4j cluster", col: "text-emerald-400" },
  { prefix: "[GOVERNANCE]", msg: "Cryptographic signature matches policy SOC2-TYPE-II", col: "text-amber-400" },
  { prefix: "[EXECUTOR]", msg: "Compiled production bundle in 3.12s. Exit status 0", col: "text-emerald-300" },
  { prefix: "[TELEMETRY]", msg: "Session #248 nominal. Streaming live telemetry metrics", col: "text-sky-400" },
];

export function HeroProductDemo() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeTab, setActiveTab] = useState<"pipeline" | "terminal" | "memory">("pipeline");
  const [selectedStep, setSelectedStep] = useState<string>("step-2");
  const [logs, setLogs] = useState(STREAMING_LOGS.slice(0, 5));
  const [logIndex, setLogIndex] = useState(5);

  // Live Metrics
  const [cpuLoad, setCpuLoad] = useState(18);
  const [memUsage, setMemUsage] = useState(38);
  const [taskProgress, setTaskProgress] = useState(64);

  // Mouse 3D Parallax Tilt
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const springConfig = { damping: 25, stiffness: 120, mass: 0.5 };
  const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [7, -7]), springConfig);
  const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-7, 7]), springConfig);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    mouseX.set(x);
    mouseY.set(y);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };

  // Live streaming log simulation
  useEffect(() => {
    const interval = setInterval(() => {
      setLogs((prev) => {
        const next = [...prev, STREAMING_LOGS[logIndex % STREAMING_LOGS.length]];
        return next.length > 8 ? next.slice(-8) : next;
      });
      setLogIndex((i) => i + 1);

      // Micro metric fluctuations
      setCpuLoad((prev) => Math.max(12, Math.min(65, prev + (Math.floor(Math.random() * 7) - 3))));
      setMemUsage((prev) => Math.max(34, Math.min(46, prev + (Math.floor(Math.random() * 3) - 1))));
      setTaskProgress((prev) => (prev >= 98 ? 32 : prev + 2));
    }, 2200);

    return () => clearInterval(interval);
  }, [logIndex]);

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative w-full perspective-[1200px] select-none py-2"
    >
      {/* Outer ambient glow behind window */}
      <div className="absolute -inset-1.5 bg-gradient-to-r from-[#22D3EE]/30 via-[#2DD4A3]/20 to-[#38BDF8]/30 rounded-3xl blur-2xl opacity-60 dark:opacity-40 -z-10 transition-opacity" />

      {/* Main 3D Browser Window Frame */}
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: "preserve-3d",
        }}
        className="w-full rounded-2xl sm:rounded-3xl border border-border/80 bg-card/90 dark:bg-[#0D1117]/95 backdrop-blur-2xl shadow-[0_20px_60px_rgba(0,0,0,0.18)] dark:shadow-[0_20px_80px_rgba(0,0,0,0.7)] overflow-hidden transition-colors"
      >
        {/* ── 1. Top Browser Header & Window Controls ─── */}
        <div className="px-4 py-3 border-b border-border/60 bg-muted/40 dark:bg-[#090B0F]/80 flex items-center justify-between gap-2">
          
          {/* Traffic light buttons */}
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[#FF5F57] inline-block shadow-sm" />
              <span className="w-3 h-3 rounded-full bg-[#FEBC2E] inline-block shadow-sm" />
              <span className="w-3 h-3 rounded-full bg-[#28C840] inline-block shadow-sm" />
            </div>
            
            {/* Tab switcher */}
            <div className="hidden sm:flex items-center gap-1 ml-3 bg-muted/60 dark:bg-black/30 p-0.5 rounded-lg border border-border/40">
              {[
                { id: "pipeline", label: "Agent Pipeline", icon: Workflow },
                { id: "terminal", label: "Live Terminal", icon: Terminal },
                { id: "memory", label: "Memory Graph", icon: Database },
              ].map((tab) => {
                const isCurrent = activeTab === tab.id;
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as "pipeline" | "terminal" | "memory")}
                    className={cn(
                      "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono transition-all",
                      isCurrent
                        ? "bg-background text-foreground font-bold shadow-sm border border-border/60"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <Icon className={cn("w-3 h-3", isCurrent ? "text-primary" : "")} />
                    {tab.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Center: Live URL Pill */}
          <div className="flex-1 max-w-[280px] hidden md:flex items-center justify-center">
            <div className="w-full flex items-center justify-between px-3 py-1 rounded-lg bg-background/80 dark:bg-black/40 border border-border/60 text-[10px] font-mono text-muted-foreground">
              <div className="flex items-center gap-1.5 truncate">
                <Lock className="w-2.5 h-2.5 text-emerald-400 flex-shrink-0" />
                <span className="text-foreground truncate">asep.cloud/session_live_248</span>
              </div>
              <span className="text-[9px] text-[#22D3EE] font-bold">LIVE</span>
            </div>
          </div>

          {/* Right Status Indicator */}
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
              <Radio className="w-2.5 h-2.5 animate-pulse" />
              60 FPS
            </span>
          </div>
        </div>

        {/* ── 2. Upper Control Plane: Live Agent Workflow Pipeline ─── */}
        <div className="p-4 sm:p-5 border-b border-border/60 bg-gradient-to-b from-muted/20 to-transparent">
          <div className="flex items-center justify-between mb-3.5">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[#22D3EE]" />
              <span className="text-xs font-mono font-bold text-foreground uppercase tracking-wider">
                Autonomous Execution Pipeline
              </span>
            </div>
            <div className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
              <span>Goal:</span>
              <span className="font-semibold text-foreground bg-accent/60 px-2 py-0.5 rounded border border-border/50 truncate max-w-[170px] sm:max-w-[260px]">
                Deploy Auth Microservice
              </span>
            </div>
          </div>

          {/* Connected Pipeline Steps */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3 relative">
            {PIPELINE_STEPS.map((step, idx) => {
              const isSelected = selectedStep === step.id;
              const StepIcon = step.icon;

              return (
                <div
                  key={step.id}
                  onClick={() => setSelectedStep(step.id)}
                  className={cn(
                    "relative p-3 rounded-xl border transition-all duration-200 cursor-pointer group flex flex-col justify-between overflow-hidden",
                    isSelected
                      ? "bg-card border-[#22D3EE]/70 shadow-[0_0_20px_rgba(34,211,238,0.15)] ring-1 ring-[#22D3EE]/50"
                      : "bg-card/60 hover:bg-card border-border/60 hover:border-border"
                  )}
                >
                  {/* Active step glow pulse */}
                  {step.status === "active" && (
                    <span
                      className="absolute top-0 right-0 w-12 h-12 bg-gradient-to-br from-[#22D3EE]/20 to-transparent rounded-bl-full pointer-events-none"
                    />
                  )}

                  <div className="flex items-center justify-between mb-2">
                    <div
                      className="w-7 h-7 rounded-lg flex items-center justify-center"
                      style={{
                        background: `${step.color}15`,
                        border: `1px solid ${step.color}40`,
                        color: step.color,
                      }}
                    >
                      <StepIcon className="w-3.5 h-3.5" />
                    </div>

                    <span
                      className={cn(
                        "text-[9px] font-mono font-bold px-1.5 py-0.5 rounded uppercase",
                        step.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : step.status === "active"
                          ? "bg-cyan-500/15 text-cyan-400 border border-cyan-500/30 animate-pulse"
                          : "bg-muted text-muted-foreground border border-border"
                      )}
                    >
                      {step.status}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-xs font-mono font-bold text-foreground group-hover:text-primary transition-colors">
                      {step.name}
                    </h4>
                    <p className="text-[10px] text-muted-foreground truncate">
                      {step.meta}
                    </p>
                  </div>

                  {/* Flow arrow on right (desktop only) */}
                  {idx < PIPELINE_STEPS.length - 1 && (
                    <div className="hidden sm:block absolute -right-2 top-1/2 -translate-y-1/2 z-10 text-border">
                      <span className="block w-1.5 h-1.5 rounded-full bg-[#22D3EE] shadow-[0_0_6px_#22D3EE]" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* ── 3. Middle & Lower Split: Terminal Logs & Real-time Telemetry ─── */}
        <div className="grid grid-cols-1 md:grid-cols-12 divide-y md:divide-y-0 md:divide-x divide-border/60 bg-card/40">
          
          {/* Left / Center (8 cols): Live Interactive Terminal */}
          <div className="md:col-span-8 p-4 flex flex-col justify-between h-[210px] sm:h-[230px] font-mono text-[11px] overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-border/40 text-muted-foreground text-[10px]">
              <div className="flex items-center gap-1.5">
                <Terminal className="w-3 h-3 text-[#22D3EE]" />
                <span className="font-bold text-foreground">sys.stdout (Live Docker Container)</span>
              </div>
              <span className="text-[#2DD4A3] flex items-center gap-1 font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2DD4A3] animate-ping" />
                EXEC STREAM
              </span>
            </div>

            {/* Logs List */}
            <div className="flex-1 py-2 overflow-y-auto space-y-1.5 flex flex-col justify-end">
              <AnimatePresence initial={false}>
                {logs.map((item, idx) => (
                  <motion.div
                    key={`${idx}-${item.msg}`}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex gap-2 items-start leading-tight"
                  >
                    <span className={cn("font-bold flex-shrink-0", item.col)}>
                      {item.prefix}
                    </span>
                    <span className="text-foreground/90 truncate">{item.msg}</span>
                  </motion.div>
                ))}
              </AnimatePresence>

              {/* Blinking cursor */}
              <div className="flex items-center gap-1.5 pt-0.5 text-primary">
                <span>&gt;</span>
                <span className="w-1.5 h-3.5 bg-[#22D3EE] animate-pulse inline-block" />
              </div>
            </div>

            {/* Bottom Terminal Status Bar */}
            <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[10px] text-muted-foreground">
              <span>Exit Code: 0</span>
              <span className="text-primary font-bold">Memory Cache: 1536d synced</span>
            </div>
          </div>

          {/* Right (4 cols): Live Telemetry Cluster Gauges */}
          <div className="md:col-span-4 p-4 flex flex-col justify-between gap-3 bg-muted/10 h-[210px] sm:h-[230px]">
            <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground pb-1.5 border-b border-border/40">
              <span className="font-bold text-foreground">Cluster Telemetry</span>
              <span className="text-[#22D3EE]">SOC2 Ready</span>
            </div>

            {/* Gauge 1: Task Progress */}
            <div>
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-muted-foreground">Task Progress</span>
                <span className="font-bold text-[#22D3EE]">{taskProgress}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-[#22D3EE] to-[#2DD4A3]"
                  animate={{ width: `${taskProgress}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>
            </div>

            {/* Gauge 2: CPU Load */}
            <div>
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Cpu className="w-2.5 h-2.5 text-[#38BDF8]" /> CPU Compute
                </span>
                <span className="font-bold text-foreground">{cpuLoad}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                <motion.div
                  className="h-full bg-[#38BDF8]"
                  animate={{ width: `${cpuLoad}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>
            </div>

            {/* Gauge 3: Memory Vector Pool */}
            <div>
              <div className="flex justify-between text-[10px] font-mono mb-1">
                <span className="text-muted-foreground flex items-center gap-1">
                  <Database className="w-2.5 h-2.5 text-[#2DD4A3]" /> Vector Store
                </span>
                <span className="font-bold text-foreground">{memUsage}%</span>
              </div>
              <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                <motion.div
                  className="h-full bg-[#2DD4A3]"
                  animate={{ width: `${memUsage}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>
            </div>

            {/* MCP Connected Tools Strip */}
            <div className="p-2 rounded-lg bg-card border border-border/60 flex items-center justify-between text-[9px] font-mono">
              <span className="text-muted-foreground">MCP TOOLS:</span>
              <div className="flex gap-1.5">
                <span className="px-1.5 py-0.5 rounded bg-muted text-[#38BDF8] border border-border/50 font-bold">
                  GitHub
                </span>
                <span className="px-1.5 py-0.5 rounded bg-muted text-[#2DD4A3] border border-border/50 font-bold">
                  Docker
                </span>
                <span className="px-1.5 py-0.5 rounded bg-muted text-[#F5B942] border border-border/50 font-bold">
                  Qdrant
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ── 4. Bottom Footer Strip: Orchestrator Status ─── */}
        <div className="px-4 py-2.5 border-t border-border/60 bg-muted/30 flex items-center justify-between text-[10px] font-mono text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#2DD4A3] shadow-[0_0_6px_#2DD4A3] animate-pulse" />
            <span className="text-foreground font-semibold">Orchestrator Node v0.1.0</span>
            <span className="hidden sm:inline">· Air-Gapped Sandbox Enforced</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-foreground font-medium">Latency: &lt;14ms</span>
            <span className="text-[#22D3EE] font-bold">All Systems Operational</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
