"use client";

import { motion } from "framer-motion";
import {
  User,
  BrainCircuit,
  Terminal,
  Database,
  Wrench,
  ShieldCheck,
  RefreshCcw,
  CheckCircle,
  LayoutDashboard,
  Flag,
} from "lucide-react";

type NodeItem = {
  id: string;
  title: string;
  description?: string;
  icon: React.ElementType;
  align: "left" | "right" | "center";
  isGroupHeader?: boolean;
  groupTitle?: string;
};

const FLOW: NodeItem[] = [
  { id: "req", title: "User Request", icon: User, align: "center" },

  // Group 1: Intelligence
  {
    id: "g1",
    title: "",
    icon: BrainCircuit,
    align: "center",
    isGroupHeader: true,
    groupTitle: "1. Intelligence",
  },
  {
    id: "plan",
    title: "Planner",
    description: "Deconstructs the request into an execution graph.",
    icon: BrainCircuit,
    align: "left",
  },
  {
    id: "exec",
    title: "Executor",
    description: "Runs the generated tasks locally.",
    icon: Terminal,
    align: "left",
  },
  {
    id: "mem",
    title: "Memory Engine",
    description: "Maintains state and context continuity.",
    icon: Database,
    align: "right",
  },

  // Group 2: Operations
  {
    id: "g2",
    title: "",
    icon: Wrench,
    align: "center",
    isGroupHeader: true,
    groupTitle: "2. Operations",
  },
  {
    id: "tool",
    title: "Tool Registry (MCP)",
    description: "Dynamically accesses external tools and APIs.",
    icon: Wrench,
    align: "right",
  },
  {
    id: "gov",
    title: "Governance",
    description: "Enforces policies and human-in-the-loop approvals.",
    icon: ShieldCheck,
    align: "left",
  },

  // Group 3: Continuous Improvement
  {
    id: "g3",
    title: "",
    icon: RefreshCcw,
    align: "center",
    isGroupHeader: true,
    groupTitle: "3. Continuous Improvement",
  },
  {
    id: "ref",
    title: "Reflection",
    description: "Analyzes execution failures and self-corrects.",
    icon: RefreshCcw,
    align: "left",
  },
  {
    id: "eval",
    title: "Evaluation",
    description: "Scores the output against the original goal.",
    icon: CheckCircle,
    align: "right",
  },
  {
    id: "ctrl",
    title: "Control Plane",
    description: "Logs traces, telemetry, and final states.",
    icon: LayoutDashboard,
    align: "right",
  },

  { id: "res", title: "Final Result", icon: Flag, align: "center" },
];

export function ArchitectureSection() {
  return (
    <section
      id="architecture"
      className="relative py-24 sm:py-32 bg-background overflow-hidden"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-20">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl"
          >
            How ASEP Works
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-4 text-lg text-muted-foreground"
          >
            A transparent, deterministic execution pipeline built for enterprise
            reliability.
          </motion.p>
        </div>

        {/* Timeline Container */}
        <div className="relative max-w-4xl mx-auto">
          {/* Central CSS Line */}
          <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-px bg-border/50 -translate-x-1/2" />

          <div className="flex flex-col space-y-12">
            {FLOW.map((node, index) => {
              const Icon = node.icon;
              const isCenter = node.align === "center";
              const isLeft = node.align === "left";

              // For group headers, display a badge in the center
              if (node.isGroupHeader) {
                return (
                  <motion.div
                    key={node.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true, margin: "-50px" }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="relative z-10 flex justify-center w-full"
                  >
                    <div className="bg-background border border-border/50 px-4 py-1.5 rounded-full shadow-sm text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center space-x-2">
                      <span>{node.groupTitle}</span>
                    </div>
                  </motion.div>
                );
              }

              // For End/Start nodes, display a centered pill
              if (isCenter) {
                return (
                  <motion.div
                    key={node.id}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: "-50px" }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                    className="relative z-10 flex justify-center w-full"
                  >
                    <div className="bg-primary/10 border border-primary/20 text-primary px-6 py-3 rounded-full shadow-lg font-bold flex items-center space-x-3 backdrop-blur-md">
                      <Icon className="h-5 w-5" />
                      <span>{node.title}</span>
                    </div>
                  </motion.div>
                );
              }

              return (
                <motion.div
                  key={node.id}
                  initial={{ opacity: 0, x: isLeft ? -20 : 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, margin: "-50px" }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className={`relative z-10 flex w-full items-center ${
                    isLeft ? "md:justify-start" : "md:justify-end"
                  }`}
                >
                  {/* Mobile overrides to act as left-aligned timeline */}
                  <div
                    className={`flex w-full md:w-1/2 ${isLeft ? "md:pr-12" : "md:pl-12"} pl-16 md:pl-0 relative`}
                  >
                    {/* Node Dot on Timeline */}
                    <div
                      className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-background border-2 border-primary z-20 ${
                        isLeft
                          ? "left-8 md:-right-2 md:left-auto"
                          : "left-8 md:-left-2"
                      } -translate-x-1/2 md:translate-x-0`}
                    />

                    {/* Card */}
                    <div
                      className={`w-full group rounded-xl border border-border/50 bg-card p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md hover:border-primary/40 ${
                        isLeft ? "md:text-right" : "md:text-left"
                      }`}
                    >
                      <div
                        className={`flex flex-col ${isLeft ? "md:items-end" : "md:items-start"} items-start space-y-2`}
                      >
                        <div className="p-2 rounded-lg bg-primary/5 text-primary mb-2 transition-colors group-hover:bg-primary/10">
                          <Icon className="h-5 w-5" />
                        </div>
                        <h3 className="font-semibold text-foreground text-lg">
                          {node.title}
                        </h3>
                        {node.description && (
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {node.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
