"use client"

import { motion } from "framer-motion"
import { BrainCircuit, Terminal, Layers, Lightbulb, ShieldCheck, LayoutDashboard } from "lucide-react"

const FEATURES = [
  {
    title: "Autonomous Planning",
    description: "Deconstructs complex objectives into deterministically executable roadmaps. ASEP plans ahead, anticipating bottlenecks before they block the pipeline.",
    icon: BrainCircuit,
    className: "md:col-span-2 lg:col-span-2 lg:row-span-2 flex flex-col justify-end p-8", // Hero card
    hero: true,
  },
  {
    title: "Intelligent Execution",
    description: "Executes multi-step plans with state-of-the-art accuracy, utilizing local context to avoid hallucination.",
    icon: Terminal,
    className: "col-span-1 p-6",
  },
  {
    title: "Multi-Layer Memory",
    description: "Maintains absolute context continuity across sessions, preventing repetitive prompting.",
    icon: Layers,
    className: "col-span-1 p-6",
  },
  {
    title: "Reflection & Learning",
    description: "Self-corrects errors in real-time, rewriting its own assumptions when tests fail.",
    icon: Lightbulb,
    className: "col-span-1 p-6",
  },
  {
    title: "Governance & Approval",
    description: "Enforces strict human-in-the-loop gates for high-risk actions, guaranteeing security.",
    icon: ShieldCheck,
    className: "col-span-1 p-6",
  },
  {
    title: "Production Control Plane",
    description: "Complete observability over agent states, execution traces, and policy health.",
    icon: LayoutDashboard,
    className: "col-span-1 md:col-span-2 lg:col-span-1 p-6",
  },
]

export function FeaturesSection() {
  return (
    <section id="platform" className="relative py-24 sm:py-32 bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl md:text-5xl"
          >
            A new standard for autonomous engineering.
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-6 text-lg text-muted-foreground"
          >
            ASEP replaces rigid pipelines with adaptive intelligence. It doesn&apos;t just write code—it plans, executes, remembers, and governs itself.
          </motion.p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-[1fr]">
          {FEATURES.map((feature, index) => {
            const Icon = feature.icon
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={`group relative rounded-2xl border border-border/50 bg-card text-card-foreground shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:border-primary/30 overflow-hidden ${feature.className}`}
              >
                {/* Subtle Gradient Glow on Hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
                
                <div className="relative z-10 h-full flex flex-col">
                  <div className={`mb-4 flex items-center justify-center rounded-lg bg-primary/10 text-primary ${feature.hero ? "h-16 w-16" : "h-12 w-12"}`}>
                    <Icon className={feature.hero ? "h-8 w-8" : "h-6 w-6"} aria-hidden="true" />
                  </div>
                  <h3 className={`font-bold text-foreground mb-2 ${feature.hero ? "text-2xl" : "text-lg"}`}>
                    {feature.title}
                  </h3>
                  <p className={`text-muted-foreground ${feature.hero ? "text-lg leading-relaxed" : "text-sm leading-relaxed"} flex-grow`}>
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </div>

      </div>
    </section>
  )
}
