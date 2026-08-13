"use client";

import { motion, useInView } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  Activity,
  BrainCircuit,
  Database,
  ShieldAlert,
  Cpu,
  ShieldCheck,
  Terminal,
  LayoutDashboard,
  ListTodo,
  CheckCircle2,
  Clock,
  Zap,
} from "lucide-react";

const INITIAL_LOGS = [
  { type: "success", prefix: "[EVAL]", message: "Agent scored 'Cache Migration' at 0.98 accuracy" },
  { type: "info", prefix: "[INFO]", message: "Context compressed and saved to Episodic Memory" },
  { type: "info", prefix: "[INFO]", message: "Awaiting next task in queue..." },
];

const LOG_POOL = [
  { type: "success", prefix: "[VERIF]", message: "TypeScript type-check returned 0 errors" },
  { type: "info", prefix: "[EXEC]", message: "Cloning workspace into isolated Docker sandbox" },
  { type: "info", prefix: "[PLAN]", message: "Decomposing goal into 4 executable subtasks" },
  { type: "success", prefix: "[BUILD]", message: "Production build completed in 3.42s — exit 0" },
  { type: "warning", prefix: "[HITL]", message: "Awaiting human approval for DB migration gate" },
  { type: "info", prefix: "[MEM]", message: "Retrieving 12 relevant chunks from Qdrant DB" },
  { type: "success", prefix: "[LINT]", message: "ESLint checks passed — 0 warnings, 0 errors" },
  { type: "info", prefix: "[CTRL]", message: "Metrics posted. Session trace written to Neo4j" },
];

interface LogEntry {
  type: string;
  prefix: string;
  message: string;
  id: number;
}

const TASKS = [
  {
    title: "Refactor Authentication Flow",
    status: "Planning",
    icon: BrainCircuit,
    color: "text-[#F5B942]",
    bgColor: "bg-[#F5B942]/10",
    borderColor: "border-[#F5B942]/30",
    progress: 22,
  },
  {
    title: "Migrate Database Schema",
    status: "Executing",
    icon: Terminal,
    color: "text-[#22D3EE]",
    bgColor: "bg-[#22D3EE]/10",
    borderColor: "border-[#22D3EE]/30",
    progress: 65,
  },
];

function MetricGauge({
  label,
  value,
  unit,
  color,
  icon: Icon,
  animate: shouldAnimate,
}: {
  label: string;
  value: number;
  unit: string;
  color: string;
  icon: React.ElementType;
  animate: boolean;
}) {
  const [displayVal, setDisplayVal] = useState(0);

  useEffect(() => {
    if (!shouldAnimate) return;
    let start = 0;
    const end = value;
    const duration = 1200;
    const step = Math.ceil(duration / end);
    const timer = setInterval(() => {
      start += 1;
      setDisplayVal(start);
      if (start >= end) clearInterval(timer);
    }, step);
    return () => clearInterval(timer);
  }, [value, shouldAnimate]);

  return (
    <div className="flex flex-col gap-2 p-3 sm:p-4 rounded-xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] group hover:border-primary/30 transition-colors shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <Icon className={`h-3.5 w-3.5 ${color}`} />
      </div>
      <div className={`text-xl sm:text-2xl font-mono font-bold ${color}`}>
        {shouldAnimate ? displayVal : value}
        <span className="text-xs sm:text-sm font-normal text-muted-foreground">{unit}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: shouldAnimate ? `${value}%` : "0%" }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className={`h-full rounded-full ${color.replace("text-", "bg-")}`}
        />
      </div>
    </div>
  );
}

export function ProductPreviewSection() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-80px" });

  const [logs, setLogs] = useState<LogEntry[]>(
    INITIAL_LOGS.map((l, i) => ({ ...l, id: i }))
  );
  const [logCounter, setLogCounter] = useState(100);
  const [cpuUsage, setCpuUsage] = useState(18);

  useEffect(() => {
    const interval = setInterval(() => {
      const randomLog = LOG_POOL[Math.floor(Math.random() * LOG_POOL.length)];
      setLogs((prev) => {
        const updated = [...prev, { ...randomLog, id: Date.now() }];
        if (updated.length > 5) updated.shift();
        return updated;
      });
      setLogCounter((c) => c + 1);
      setCpuUsage(() => Math.max(10, Math.min(65, Math.floor(Math.random() * 50) + 10)));
    }, 2600);

    return () => clearInterval(interval);
  }, []);

  const logColors: Record<string, string> = {
    success: "text-[#2DD4A3]",
    info: "text-[#38BDF8]",
    warning: "text-[#F5B942]",
    error: "text-[#F05252]",
  };

  const prefixColors: Record<string, string> = {
    success: "text-[#2DD4A3]",
    info: "text-[#22D3EE]",
    warning: "text-[#F5B942]",
    error: "text-red-400",
  };

  return (
    <section
      id="product"
      ref={sectionRef}
      className="relative py-20 sm:py-28 md:py-32 bg-background dark:bg-[#090B0F] overflow-hidden border-b border-border transition-colors duration-300"
    >
      {/* Background effects */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[#22D3EE]/3 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[200px] bg-[#2DD4A3]/3 rounded-full blur-[100px] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-14 sm:mb-16 space-y-3 sm:space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
            className="flex justify-center"
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117]/80 px-3 py-1 text-xs font-mono font-medium text-primary shadow-sm">
              <LayoutDashboard className="h-3.5 w-3.5" />
              CONTROL PLANE
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground font-sans"
          >
            Full Observability.{" "}
            <span className="text-primary">Zero Blind Spots.</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-base sm:text-lg text-muted-foreground font-sans max-w-2xl mx-auto leading-relaxed"
          >
            Real-time telemetry, agent task queues, governance gates, and memory
            diagnostics — all in a unified control plane built for production workloads.
          </motion.p>
        </div>

        {/* Dashboard Window */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="relative mx-auto max-w-6xl"
        >
          {/* Outer glow ring */}
          <div className="absolute -inset-[1px] rounded-2xl bg-gradient-to-b from-[#22D3EE]/20 via-transparent to-[#2DD4A3]/10 pointer-events-none" />

          {/* Browser chrome */}
          <div className="relative rounded-2xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#090B0F] shadow-[0_20px_60px_rgba(0,0,0,0.12)] dark:shadow-[0_40px_120px_rgba(0,0,0,0.8)] overflow-hidden">

            {/* Browser title bar */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-border/80 dark:border-[#202833] bg-muted/40 dark:bg-[#0D1117]">
              <div className="flex gap-1.5">
                <div className="h-3 w-3 rounded-full bg-red-500/70" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/70" />
                <div className="h-3 w-3 rounded-full bg-green-500/70" />
              </div>
              <div className="flex-1 mx-4">
                <div className="max-w-xs mx-auto bg-background/80 dark:bg-[#111720] border border-border/60 rounded-md px-3 py-1 text-[10px] font-mono text-muted-foreground flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#2DD4A3] animate-pulse" />
                  asep.local/control-plane/overview
                </div>
              </div>
              <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground">
                <span>ASEP v0.1.0</span>
              </div>
            </div>

            {/* App layout */}
            <div className="flex min-h-[540px]">

              {/* Sidebar */}
              <div className="hidden md:flex w-52 lg:w-56 border-r border-border/80 dark:border-[#202833] bg-muted/20 dark:bg-[#0D1117] flex-col">
                <div className="flex items-center gap-2 px-4 py-4 border-b border-border/80 dark:border-[#202833]">
                  <div className="p-1 rounded-lg bg-primary/10 border border-primary/20 text-primary">
                    <Cpu className="h-3.5 w-3.5" />
                  </div>
                  <span className="text-xs font-mono font-bold text-foreground tracking-wider">ASEP CONTROL</span>
                </div>

                <nav className="flex-1 p-3 space-y-1 font-mono text-xs">
                  {[
                    { name: "Overview", icon: LayoutDashboard, active: true },
                    { name: "Active Agents", icon: BrainCircuit, badge: "6" },
                    { name: "Task Queue", icon: ListTodo, badge: "2" },
                    { name: "Memory", icon: Database },
                    { name: "Governance", icon: ShieldCheck, badge: "1", badgeColor: "text-[#F5B942] bg-[#F5B942]/10 border-[#F5B942]/20" },
                  ].map((item) => (
                    <div
                      key={item.name}
                      className={`flex items-center justify-between px-3 py-2 rounded-lg transition-colors cursor-pointer ${
                        item.active
                          ? "bg-accent text-foreground font-semibold border border-border"
                          : "text-muted-foreground hover:bg-accent hover:text-foreground"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <item.icon className={`h-3.5 w-3.5 ${item.active ? "text-primary" : ""}`} />
                        <span>{item.name}</span>
                      </div>
                      {item.badge && (
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full border font-bold ${item.badgeColor || "text-primary bg-primary/10 border-primary/20"}`}>
                          {item.badge}
                        </span>
                      )}
                    </div>
                  ))}
                </nav>

                <div className="p-3 border-t border-border/80 dark:border-[#202833]">
                  <div className="p-3 rounded-lg bg-card dark:bg-[#111720] border border-border/80 dark:border-[#202833] text-xs font-mono space-y-1">
                    <div className="flex items-center gap-1.5 text-[#2DD4A3]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#2DD4A3] animate-pulse" />
                      <span className="font-bold text-[10px]">SYSTEM HEALTHY</span>
                    </div>
                    <div className="text-muted-foreground text-[10px]">Uptime: 99.98%</div>
                  </div>
                </div>
              </div>

              {/* Main content */}
              <div className="flex-1 flex flex-col bg-card/60 dark:bg-[#090B0F] overflow-hidden">

                {/* Top bar */}
                <div className="flex items-center justify-between px-4 sm:px-6 py-3.5 border-b border-border/80 dark:border-[#202833]">
                  <div className="flex items-center gap-2.5">
                    <Terminal className="h-4 w-4 text-primary" />
                    <h3 className="font-mono text-sm font-bold text-foreground">System Overview</h3>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-mono text-muted-foreground">Log #{logCounter}</span>
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#2DD4A3] bg-[#2DD4A3]/10 border border-[#2DD4A3]/20 px-2 py-0.5 rounded-full font-bold">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#2DD4A3] animate-pulse" />
                      OPERATIONAL
                    </div>
                  </div>
                </div>

                {/* Metrics row */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 p-4 sm:p-6 border-b border-border/80 dark:border-[#202833]">
                  <MetricGauge
                    label="CPU Load"
                    value={cpuUsage}
                    unit="%"
                    color="text-[#22D3EE]"
                    icon={Cpu}
                    animate={isInView}
                  />
                  <MetricGauge
                    label="Memory"
                    value={38}
                    unit="%"
                    color="text-[#2DD4A3]"
                    icon={Database}
                    animate={isInView}
                  />
                  <div className="flex flex-col gap-2 p-3 sm:p-4 rounded-xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] hover:border-primary/30 transition-colors shadow-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-muted-foreground">
                        Agents Active
                      </span>
                      <Zap className="h-3.5 w-3.5 text-[#F5B942]" />
                    </div>
                    <div className="text-xl sm:text-2xl font-mono font-bold text-[#F5B942]">
                      6
                      <span className="text-xs sm:text-sm font-normal text-muted-foreground ml-1">nodes</span>
                    </div>
                    <div className="text-[10px] font-mono text-muted-foreground flex items-center gap-1.5">
                      <CheckCircle2 className="h-3 w-3 text-[#2DD4A3]" />
                      3 Planners · 3 Executors
                    </div>
                  </div>
                </div>

                {/* Task queue + Governance row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 sm:p-6 border-b border-border/80 dark:border-[#202833]">
                  {/* Task queue */}
                  <div className="rounded-xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] overflow-hidden shadow-sm">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-border/80 dark:border-[#202833]">
                      <div className="flex items-center gap-2">
                        <ListTodo className="h-3.5 w-3.5 text-primary" />
                        <h4 className="font-mono text-xs font-bold text-foreground">Active Task Queue</h4>
                      </div>
                      <div className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-bold">
                        {TASKS.length} RUNNING
                      </div>
                    </div>
                    <div className="p-3 space-y-2">
                      {TASKS.map((task, i) => (
                        <div
                          key={i}
                          className={`flex flex-col gap-2 p-3 rounded-lg border ${task.borderColor} ${task.bgColor}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <task.icon className={`h-3.5 w-3.5 ${task.color}`} />
                              <span className="text-xs font-mono text-foreground font-medium">{task.title}</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <Clock className="h-3 w-3 text-muted-foreground" />
                              <span className={`text-[10px] font-mono ${task.color}`}>{task.status}</span>
                            </div>
                          </div>
                          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                            <motion.div
                              initial={{ width: 0 }}
                              whileInView={{ width: `${task.progress}%` }}
                              viewport={{ once: true }}
                              transition={{ duration: 1, delay: i * 0.2 }}
                              className={`h-full rounded-full ${task.color.replace("text-", "bg-")}`}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Governance */}
                  <div className="rounded-xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] overflow-hidden shadow-sm">
                    <div className="flex items-center justify-between px-4 py-3 border-b border-border/80 dark:border-[#202833]">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="h-3.5 w-3.5 text-[#2DD4A3]" />
                        <h4 className="font-mono text-xs font-bold text-foreground">Governance Gates</h4>
                      </div>
                      <div className="text-[9px] font-mono px-2 py-0.5 rounded-full bg-[#F5B942]/10 text-[#F5B942] border border-[#F5B942]/20 font-bold">
                        1 PENDING
                      </div>
                    </div>
                    <div className="p-3.5">
                      <div className="p-3.5 rounded-xl border border-[#F5B942]/30 bg-[#F5B942]/5 space-y-2.5">
                        <div className="flex items-center gap-2">
                          <ShieldAlert className="h-4 w-4 text-[#F5B942]" />
                          <span className="text-xs font-mono font-bold text-[#F5B942]">
                            Production Deployment Gate
                          </span>
                        </div>
                        <p className="text-[11px] font-mono text-muted-foreground leading-relaxed">
                          Executor requesting authorization to run production DB migration.
                          Awaiting HITL approval from authorized operator.
                        </p>
                        <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground">
                          <Activity className="h-3 w-3" />
                          <span>Cryptographic signature required</span>
                        </div>
                        <div className="flex gap-2 pt-1">
                          <div className="flex-1 text-center py-1.5 rounded-lg bg-[#22D3EE] text-[#090B0F] text-[11px] font-mono font-bold cursor-default shadow-sm">
                            Approve
                          </div>
                          <div className="flex-1 text-center py-1.5 rounded-lg border border-border bg-muted/60 text-muted-foreground text-[11px] font-mono cursor-default">
                            Reject
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Telemetry log */}
                <div className="flex-1 p-4 sm:p-6">
                  <div className="rounded-xl border border-border/80 dark:border-[#202833] bg-card/90 dark:bg-[#080A0E] overflow-hidden h-full min-h-[140px] shadow-sm">
                    <div className="flex items-center justify-between px-4 py-2.5 border-b border-border/80 dark:border-[#202833] bg-muted/30">
                      <div className="flex items-center gap-2">
                        <Activity className="h-3.5 w-3.5 text-primary" />
                        <h4 className="font-mono text-xs font-bold text-foreground">Telemetry Stream</h4>
                      </div>
                      <div className="flex items-center gap-2 text-[10px] font-mono text-muted-foreground">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#2DD4A3] animate-pulse" />
                        <span className="text-[#2DD4A3] font-bold">LIVE</span>
                      </div>
                    </div>
                    <div className="p-3.5 font-mono text-[11px] space-y-1.5 overflow-hidden">
                      {logs.map((log) => (
                        <motion.div
                          key={log.id}
                          initial={{ opacity: 0, x: -6 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2 }}
                          className="flex gap-2 items-start"
                        >
                          <span className="text-muted-foreground/50 select-none">&gt;</span>
                          <span className={`${prefixColors[log.type] || "text-primary"} font-bold shrink-0`}>
                            {log.prefix}
                          </span>
                          <span className={`${logColors[log.type] || "text-muted-foreground"} break-all`}>
                            {log.message}
                          </span>
                        </motion.div>
                      ))}
                      <div className="flex items-center gap-1 text-primary/70 pt-0.5">
                        <span>&gt;</span>
                        <span className="w-1.5 h-3 bg-primary animate-pulse inline-block" />
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
