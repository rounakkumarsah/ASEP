"use client";

import { motion } from "framer-motion";
import {
  Server,
  Database,
  Package,
  Code2,
  Network,
  Braces,
  Quote,
  User,
} from "lucide-react";

const TECHNOLOGIES = [
  { name: "FastAPI", icon: Code2 },
  { name: "PostgreSQL", icon: Database },
  { name: "Redis", icon: Server },
  { name: "Docker", icon: Package },
  { name: "LangGraph", icon: Network },
  { name: "Ollama", icon: Braces },
];

const METRICS = [
  { value: "6", label: "Core Autonomous Agents" },
  { value: "3", label: "Enterprise Memory Layers" },
  { value: "5+", label: "Strict Governance Policies" },
  { value: "100%", label: "Local-First Execution" },
];

export function SocialProofSection() {
  return (
    <section className="relative overflow-hidden bg-background py-16 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Technology Grid */}
        <div className="mb-20">
          <p className="text-center text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-8">
            Powered by modern AI infrastructure
          </p>
          <div className="grid grid-cols-2 gap-8 md:grid-cols-3 lg:grid-cols-6 opacity-70">
            {TECHNOLOGIES.map((tech, index) => {
              const Icon = tech.icon;
              return (
                <motion.div
                  key={tech.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="flex flex-col items-center justify-center space-y-2 text-muted-foreground transition-all hover:text-foreground hover:scale-105"
                >
                  <Icon className="h-8 w-8" />
                  <span className="text-sm font-medium">{tech.name}</span>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Divider */}
        <div className="mx-auto max-w-3xl border-t border-border/50 mb-20" />

        {/* Metrics & Testimonial Container */}
        <div className="grid gap-16 lg:grid-cols-2 lg:gap-8 items-center">
          {/* Capability Metrics */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl mb-8">
              Built for production scale.
            </h2>
            <div className="grid grid-cols-2 gap-x-8 gap-y-10">
              {METRICS.map((metric) => (
                <div key={metric.label}>
                  <div className="text-3xl font-extrabold text-primary sm:text-4xl">
                    {metric.value}
                  </div>
                  <div className="mt-2 text-sm text-muted-foreground">
                    {metric.label}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Testimonial Placeholder */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <div className="absolute -inset-1 rounded-xl bg-gradient-to-r from-primary/20 to-primary/0 blur-xl opacity-50" />
            <div className="relative rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md p-8 shadow-2xl">
              <Quote className="h-10 w-10 text-primary/40 mb-6" />
              <blockquote className="text-xl leading-relaxed text-muted-foreground italic mb-6">
                &quot;Early access feedback and customer testimonials will
                appear here once the platform moves into the next phase of
                deployment.&quot;
              </blockquote>
              <div className="flex items-center space-x-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted/30">
                  <User className="h-6 w-6 text-muted-foreground" />
                </div>
                <div>
                  <div className="font-semibold text-foreground">
                    Early Adopter
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Engineering Leader
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
