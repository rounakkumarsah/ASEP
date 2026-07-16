"use client";

import { motion } from "framer-motion";
import {
  Activity,
  BrainCircuit,
  Database,
  ShieldAlert,
  Cpu,
  ShieldCheck,
  Terminal,
} from "lucide-react";

export function ProductPreviewSection() {
  const containerVariants = {
    hidden: { opacity: 0, y: 40 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.7,
        when: "beforeChildren",
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  };

  return (
    <section className="relative py-24 sm:py-32 bg-background overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl"
          >
            Observe and control everything.
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-4 text-lg text-muted-foreground"
          >
            A high-fidelity preview of the ASEP Control Plane. Total
            observability into agent states, memory, and governance.
          </motion.p>
        </div>

        {/* Dashboard Preview Container */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={containerVariants}
          className="relative mx-auto max-w-6xl"
        >
          {/* Subtle Container Glow */}
          <div className="absolute -inset-1 rounded-3xl bg-gradient-to-b from-primary/20 to-primary/0 blur-2xl opacity-50 -z-10" />

          {/* Dashboard Window */}
          <div className="relative rounded-2xl border border-border/50 bg-black/40 backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col md:flex-row min-h-[600px]">
            {/* Sidebar (Desktop only) */}
            <div className="hidden md:flex w-64 border-r border-border/50 bg-card/30 flex-col p-4">
              <div className="flex items-center space-x-2 px-2 py-4 mb-4">
                <div className="h-3 w-3 rounded-full bg-red-500/80" />
                <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
                <div className="h-3 w-3 rounded-full bg-green-500/80" />
              </div>
              <nav className="space-y-1">
                {[
                  { name: "Overview", icon: LayoutDashboard, active: true },
                  { name: "Active Agents", icon: BrainCircuit },
                  { name: "Task Queue", icon: ListTodo },
                  { name: "Memory", icon: Database },
                  { name: "Governance", icon: ShieldCheck },
                ].map((item) => (
                  <div
                    key={item.name}
                    className={`flex items-center space-x-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${item.active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-muted/50 hover:text-foreground"}`}
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </div>
                ))}
              </nav>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 p-6 lg:p-8 flex flex-col space-y-6 overflow-hidden">
              {/* Top Row: Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Metric 1 */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-xl border border-border/50 bg-card/50 p-5"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-medium text-muted-foreground">
                      System Health
                    </span>
                    <Activity className="h-4 w-4 text-green-500" />
                  </div>
                  <div className="text-2xl font-bold text-foreground">
                    99.99%
                  </div>
                  <div className="mt-1 flex items-center text-xs text-muted-foreground">
                    <span className="text-green-500 mr-1">↑ Operational</span>
                    <span>Lat: 12ms</span>
                  </div>
                </motion.div>

                {/* Metric 2 */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-xl border border-border/50 bg-card/50 p-5"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-sm font-medium text-muted-foreground">
                      Active Agents
                    </span>
                    <Cpu className="h-4 w-4 text-primary" />
                  </div>
                  <div className="text-2xl font-bold text-foreground">24</div>
                  <div className="mt-1 flex items-center text-xs text-muted-foreground">
                    <span>12 Planners, 12 Executors</span>
                  </div>
                </motion.div>

                {/* Metric 3 */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-xl border border-border/50 bg-card/50 p-5"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-muted-foreground">
                      Memory Usage
                    </span>
                    <Database className="h-4 w-4 text-blue-500" />
                  </div>
                  <div className="text-2xl font-bold text-foreground">64%</div>
                  <div className="mt-3 h-1.5 w-full bg-muted overflow-hidden rounded-full">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: "64%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, delay: 0.5 }}
                      className="h-full bg-blue-500 rounded-full"
                    />
                  </div>
                </motion.div>
              </div>

              {/* Middle Row: Queue & Governance */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Planner Queue */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-xl border border-border/50 bg-card/50 flex flex-col"
                >
                  <div className="p-4 border-b border-border/50 flex items-center justify-between">
                    <h3 className="font-semibold text-sm">Active Task Queue</h3>
                    <div className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium">
                      3 Running
                    </div>
                  </div>
                  <div className="p-4 space-y-4">
                    {[
                      {
                        title: "Refactor Authentication Flow",
                        status: "Planning",
                        icon: BrainCircuit,
                        color: "text-yellow-500",
                      },
                      {
                        title: "Migrate Database Schema",
                        status: "Executing",
                        icon: Terminal,
                        color: "text-blue-500",
                      },
                      {
                        title: "Optimize Image Assets",
                        status: "Executing",
                        icon: Terminal,
                        color: "text-blue-500",
                      },
                    ].map((task, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-3 rounded-lg border border-border/30 bg-muted/20 hover:bg-muted/40 transition-colors"
                      >
                        <div className="flex items-center space-x-3">
                          <task.icon className={`h-4 w-4 ${task.color}`} />
                          <span className="text-sm font-medium">
                            {task.title}
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {task.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>

                {/* Governance Queue */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-xl border border-border/50 bg-card/50 flex flex-col"
                >
                  <div className="p-4 border-b border-border/50 flex items-center justify-between">
                    <h3 className="font-semibold text-sm">
                      Governance Approvals
                    </h3>
                    <div className="px-2 py-0.5 rounded-full bg-destructive/10 text-destructive text-xs font-medium">
                      1 Pending
                    </div>
                  </div>
                  <div className="p-4 space-y-4">
                    <div className="p-4 rounded-lg border border-destructive/20 bg-destructive/5">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <ShieldAlert className="h-4 w-4 text-destructive" />
                          <span className="text-sm font-semibold text-destructive">
                            Production Deployment
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          Just now
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mb-4">
                        Executor agent is requesting permission to execute
                        `terraform apply` in production environment.
                      </p>
                      <div className="flex space-x-2">
                        <div className="flex-1 text-center py-1.5 rounded bg-primary text-primary-foreground text-xs font-medium cursor-not-allowed opacity-80">
                          Approve
                        </div>
                        <div className="flex-1 text-center py-1.5 rounded border border-border bg-background text-xs font-medium cursor-not-allowed opacity-80">
                          Reject
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Bottom Row: Logs */}
              <motion.div
                variants={itemVariants}
                className="rounded-xl border border-border/50 bg-card/50 flex flex-col flex-1 min-h-[150px]"
              >
                <div className="p-4 border-b border-border/50 flex items-center justify-between">
                  <h3 className="font-semibold text-sm">Evaluation Logs</h3>
                  <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                    <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                    <span>Live</span>
                  </div>
                </div>
                <div className="p-4 font-mono text-xs text-muted-foreground space-y-2 overflow-hidden flex-1">
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.6 }}
                  >
                    <span className="text-green-500 mr-2">[SUCCESS]</span> Eval
                    agent scored execution &apos;Cache Migration&apos; at 0.98.
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.8 }}
                  >
                    <span className="text-blue-500 mr-2">[INFO]</span> Context
                    compressed and saved to Long-Term Memory.
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 1.0 }}
                  >
                    <span className="text-blue-500 mr-2">[INFO]</span> Awaiting
                    next task in queue...
                  </motion.div>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

// Missing icon imports added locally for the array
function LayoutDashboard(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="7" height="9" x="3" y="3" rx="1" />
      <rect width="7" height="5" x="14" y="3" rx="1" />
      <rect width="7" height="9" x="14" y="12" rx="1" />
      <rect width="7" height="5" x="3" y="16" rx="1" />
    </svg>
  );
}
function ListTodo(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3" y="5" width="6" height="6" rx="1" />
      <path d="m3 17 2 2 4-4" />
      <path d="M13 6h8" />
      <path d="M13 12h8" />
      <path d="M13 18h8" />
    </svg>
  );
}
