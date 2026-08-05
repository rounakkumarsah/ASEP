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
  LayoutDashboard,
  ListTodo
} from "lucide-react";

export function ProductPreviewSection() {
  const containerVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        when: "beforeChildren",
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4 },
    },
  };

  return (
    <section className="relative py-24 sm:py-32 bg-[#090B0F] overflow-hidden border-b border-[#202833]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-16 space-y-3">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-extrabold tracking-tight text-[#F5F7FA] sm:text-4xl font-sans"
          >
            Engineering Observability & Control
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-base text-[#9CA6B5] font-sans"
          >
            Total visibility into agent states, memory layers, and human-in-the-loop governance.
          </motion.p>
        </div>

        {/* Dashboard Window */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={containerVariants}
          className="relative mx-auto max-w-6xl"
        >
          <div className="relative rounded-xl border border-[#202833] bg-[#0D1117] shadow-2xl overflow-hidden flex flex-col md:flex-row min-h-[580px]">
            {/* Sidebar (Desktop only) */}
            <div className="hidden md:flex w-64 border-r border-[#202833] bg-[#0D1117] flex-col p-4 space-y-4">
              <div className="flex items-center space-x-2 px-2 py-2 border-b border-[#202833]">
                <Cpu className="h-4 w-4 text-[#22D3EE]" />
                <span className="text-xs font-mono font-bold text-[#F5F7FA]">ASEP CONTROL</span>
              </div>
              <nav className="space-y-1 font-mono text-xs">
                {[
                  { name: "Overview", icon: LayoutDashboard, active: true },
                  { name: "Active Agents", icon: BrainCircuit },
                  { name: "Task Queue", icon: ListTodo },
                  { name: "Memory", icon: Database },
                  { name: "Governance", icon: ShieldCheck },
                ].map((item) => (
                  <div
                    key={item.name}
                    className={`flex items-center space-x-3 px-3 py-2 rounded-md transition-colors ${item.active ? "bg-[#111720] text-[#F5F7FA] border-l-2 border-[#22D3EE] font-semibold" : "text-[#667085] hover:bg-[#111720]/60 hover:text-[#9CA6B5]"}`}
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </div>
                ))}
              </nav>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 p-6 lg:p-8 flex flex-col space-y-6 overflow-hidden bg-[#090B0F]">
              {/* Top Row: Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* Metric 1 */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-lg border border-[#202833] bg-[#0D1117] p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">
                      System Health
                    </span>
                    <Activity className="h-4 w-4 text-[#2DD4A3]" />
                  </div>
                  <div className="text-xl font-mono font-bold text-[#F5F7FA]">
                    99.9%
                  </div>
                  <div className="mt-1 flex items-center text-[10px] font-mono text-[#667085]">
                    <span className="text-[#2DD4A3] mr-1">Operational</span>
                    <span>• Latency: 12ms</span>
                  </div>
                </motion.div>

                {/* Metric 2 */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-lg border border-[#202833] bg-[#0D1117] p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">
                      Active Agents
                    </span>
                    <Cpu className="h-4 w-4 text-[#22D3EE]" />
                  </div>
                  <div className="text-xl font-mono font-bold text-[#F5F7FA]">6</div>
                  <div className="mt-1 flex items-center text-[10px] font-mono text-[#667085]">
                    <span>3 Planners, 3 Executors</span>
                  </div>
                </motion.div>

                {/* Metric 3 */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-lg border border-[#202833] bg-[#0D1117] p-4"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">
                      Memory Usage
                    </span>
                    <Database className="h-4 w-4 text-[#38BDF8]" />
                  </div>
                  <div className="text-xl font-mono font-bold text-[#F5F7FA]">38%</div>
                  <div className="mt-2 h-1.5 w-full bg-[#111720] overflow-hidden rounded-full border border-[#202833]">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: "38%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, delay: 0.3 }}
                      className="h-full bg-[#22D3EE] rounded-full"
                    />
                  </div>
                </motion.div>
              </div>

              {/* Middle Row: Queue & Governance */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Planner Queue */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-lg border border-[#202833] bg-[#0D1117] flex flex-col"
                >
                  <div className="p-3 border-b border-[#202833] flex items-center justify-between">
                    <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F5F7FA]">Active Task Queue</h3>
                    <div className="px-2 py-0.5 rounded bg-[#22D3EE]/10 text-[#22D3EE] text-[10px] font-mono font-medium border border-[#22D3EE]/20">
                      2 Running
                    </div>
                  </div>
                  <div className="p-3 space-y-2">
                    {[
                      {
                        title: "Refactor Authentication Flow",
                        status: "Planning",
                        icon: BrainCircuit,
                        color: "text-[#F5B942]",
                      },
                      {
                        title: "Migrate Database Schema",
                        status: "Executing",
                        icon: Terminal,
                        color: "text-[#22D3EE]",
                      },
                    ].map((task, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-2.5 rounded border border-[#202833] bg-[#111720]/50 font-mono text-xs"
                      >
                        <div className="flex items-center space-x-2.5">
                          <task.icon className={`h-4 w-4 ${task.color}`} />
                          <span className="text-[#F5F7FA]">
                            {task.title}
                          </span>
                        </div>
                        <span className="text-[10px] text-[#667085]">
                          {task.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>

                {/* Governance Queue */}
                <motion.div
                  variants={itemVariants}
                  className="rounded-lg border border-[#202833] bg-[#0D1117] flex flex-col"
                >
                  <div className="p-3 border-b border-[#202833] flex items-center justify-between">
                    <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F5F7FA]">
                      Governance Approvals
                    </h3>
                    <div className="px-2 py-0.5 rounded bg-[#F5B942]/10 text-[#F5B942] text-[10px] font-mono font-medium border border-[#F5B942]/20">
                      1 Pending
                    </div>
                  </div>
                  <div className="p-3">
                    <div className="p-3 rounded border border-[#F5B942]/30 bg-[#F5B942]/5 font-mono">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <ShieldAlert className="h-4 w-4 text-[#F5B942]" />
                          <span className="text-xs font-bold text-[#F5B942]">
                            Production Deployment Gate
                          </span>
                        </div>
                      </div>
                      <p className="text-[11px] text-[#9CA6B5] mb-3">
                        Executor agent requesting authorization to run production migration.
                      </p>
                      <div className="flex space-x-2">
                        <div className="flex-1 text-center py-1 rounded bg-[#22D3EE] text-[#090B0F] text-[11px] font-bold cursor-not-allowed opacity-90">
                          Approve
                        </div>
                        <div className="flex-1 text-center py-1 rounded border border-[#202833] bg-[#111720] text-[#F5F7FA] text-[11px] font-semibold cursor-not-allowed opacity-90">
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
                className="rounded-lg border border-[#202833] bg-[#0D1117] flex flex-col flex-1 min-h-[140px]"
              >
                <div className="p-3 border-b border-[#202833] flex items-center justify-between">
                  <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-[#F5F7FA]">Telemetry Log Stream</h3>
                  <div className="flex items-center space-x-2 text-[10px] font-mono text-[#9CA6B5]">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#2DD4A3] animate-pulse" />
                    <span>Streaming</span>
                  </div>
                </div>
                <div className="p-3 font-mono text-[11px] text-[#9CA6B5] space-y-1.5 overflow-hidden flex-1">
                  <div>
                    <span className="text-[#2DD4A3] mr-2">[SUCCESS]</span> Eval agent scored execution &apos;Cache Migration&apos; at 0.98 accuracy.
                  </div>
                  <div>
                    <span className="text-[#38BDF8] mr-2">[INFO]</span> Context compressed and saved to Episodic Memory.
                  </div>
                  <div>
                    <span className="text-[#38BDF8] mr-2">[INFO]</span> Awaiting next task in queue...
                  </div>
                </div>
              </motion.div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
