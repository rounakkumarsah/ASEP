"use client";

import { motion } from "framer-motion";
import {
  BrainCircuit,
  Terminal,
  Layers,
  Lightbulb,
  ShieldCheck,
  LayoutDashboard,
} from "lucide-react";

const FEATURES = [
  {
    title: "Autonomous Planning",
    description:
      "Deconstructs complex objectives into deterministically executable roadmaps. ASEP plans ahead, anticipating bottlenecks before they block the pipeline.",
    icon: BrainCircuit,
    className:
      "md:col-span-2 lg:col-span-2 lg:row-span-2 flex flex-col justify-end p-8",
    hero: true,
  },
  {
    title: "Intelligent Execution",
    description:
      "Executes multi-step plans with state-of-the-art accuracy, utilizing verified workspace context to avoid hallucination.",
    icon: Terminal,
    className: "col-span-1 p-6",
  },
  {
    title: "Multi-Layer Memory",
    description:
      "Maintains absolute context continuity across sessions, preventing repetitive prompting and context loss.",
    icon: Layers,
    className: "col-span-1 p-6",
  },
  {
    title: "Reflection & Learning",
    description:
      "Self-corrects execution errors in real-time, rewriting assumptions when verification suites fail.",
    icon: Lightbulb,
    className: "col-span-1 p-6",
  },
  {
    title: "Governance & Approval",
    description:
      "Enforces strict human-in-the-loop policy gates for high-risk system actions.",
    icon: ShieldCheck,
    className: "col-span-1 p-6",
  },
  {
    title: "Production Control Plane",
    description:
      "Complete observability over agent states, execution traces, and telemetry health.",
    icon: LayoutDashboard,
    className: "col-span-1 md:col-span-2 lg:col-span-1 p-6",
  },
];

export function FeaturesSection() {
  return (
    <section id="platform" className="relative py-24 sm:py-32 bg-[#090B0F] border-b border-[#202833]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-16 space-y-4">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-extrabold tracking-tight text-[#F5F7FA] sm:text-4xl md:text-5xl font-sans"
          >
            Engineered for Production Autonomy
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-base text-[#9CA6B5] font-sans"
          >
            ASEP replaces brittle scripts with an adaptive engineering control plane. It plans, executes, remembers, and governs itself.
          </motion.p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-[1fr]">
          {FEATURES.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`group relative rounded-xl border border-[#202833] bg-[#0D1117] text-[#F5F7FA] transition-all duration-200 hover:border-[#22D3EE]/40 overflow-hidden ${feature.className}`}
              >
                <div className="relative z-10 h-full flex flex-col">
                  <div
                    className={`mb-4 flex items-center justify-center rounded-md bg-[#111720] border border-[#202833] text-[#22D3EE] ${feature.hero ? "h-14 w-14" : "h-10 w-10"}`}
                  >
                    <Icon
                      className={feature.hero ? "h-7 w-7" : "h-5 w-5"}
                      aria-hidden="true"
                    />
                  </div>
                  <h3
                    className={`font-bold text-[#F5F7FA] mb-2 font-sans ${feature.hero ? "text-xl" : "text-base"}`}
                  >
                    {feature.title}
                  </h3>
                  <p
                    className={`text-[#9CA6B5] font-sans ${feature.hero ? "text-sm leading-relaxed" : "text-xs leading-relaxed"} flex-grow`}
                  >
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
