"use client";

import React, { forwardRef, useRef } from "react";
import { cn } from "@/lib/utils";
import { AnimatedBeam } from "@/components/ui/animated-beam";
import { motion } from "framer-motion";
import {
  Github,
  Slack,
  Box,
  Database,
  Webhook,
  Cloud,
  Cpu,
  Network,
} from "lucide-react";

interface CircleProps {
  className?: string;
  children?: React.ReactNode;
  label: string;
  glow?: boolean;
}

const IntegrationNode = forwardRef<HTMLDivElement, CircleProps>(
  ({ className, children, label, glow = false }, ref) => {
    return (
      <div className="flex flex-col items-center gap-2">
        <div
          ref={ref}
          className={cn(
            "relative z-10 flex size-12 sm:size-14 items-center justify-center rounded-2xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] p-2.5 sm:p-3 transition-all duration-300 hover:border-primary/50 hover:scale-105 cursor-pointer group shadow-sm",
            glow &&
              "border-primary/50 bg-primary/5 shadow-[0_0_25px_rgba(34,211,238,0.25)]",
            className
          )}
        >
          {children}
          {glow && (
            <div className="absolute inset-0 rounded-2xl bg-primary/10 animate-pulse" />
          )}
        </div>
        <span className="text-[9px] font-mono font-bold tracking-wider uppercase text-muted-foreground group-hover:text-foreground">
          {label}
        </span>
      </div>
    );
  }
);
IntegrationNode.displayName = "IntegrationNode";

const INTEGRATION_CARDS = [
  {
    title: "Source Control",
    tools: ["GitHub", "GitLab", "Bitbucket"],
    description: "Agents commit, create PRs, and manage branches natively",
    color: "border-[#22D3EE]/30 bg-[#22D3EE]/5",
    accent: "text-[#22D3EE]",
  },
  {
    title: "Notifications",
    tools: ["Slack", "Teams", "Email"],
    description: "Real-time governance alerts and execution status updates",
    color: "border-[#2DD4A3]/30 bg-[#2DD4A3]/5",
    accent: "text-[#2DD4A3]",
  },
  {
    title: "Infrastructure",
    tools: ["Docker", "K8s", "VPC"],
    description: "Isolated, resource-limited sandbox environments per task",
    color: "border-[#F5B942]/30 bg-[#F5B942]/5",
    accent: "text-[#F5B942]",
  },
  {
    title: "Cloud Storage",
    tools: ["S3", "GCS", "Azure Blob"],
    description: "Artifact storage, audit logs, and memory persistence layers",
    color: "border-[#38BDF8]/30 bg-[#38BDF8]/5",
    accent: "text-[#38BDF8]",
  },
  {
    title: "Webhooks & APIs",
    tools: ["REST", "GraphQL", "gRPC"],
    description: "Trigger agents from external events and CI/CD pipelines",
    color: "border-[#818CF8]/30 bg-[#818CF8]/5",
    accent: "text-[#818CF8]",
  },
  {
    title: "Databases",
    tools: ["PostgreSQL", "Redis", "Qdrant"],
    description: "Structured state, distributed cache, and semantic memory",
    color: "border-[#FB7185]/30 bg-[#FB7185]/5",
    accent: "text-[#FB7185]",
  },
];

export function IntegrationsSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const div1Ref = useRef<HTMLDivElement>(null);
  const div2Ref = useRef<HTMLDivElement>(null);
  const div3Ref = useRef<HTMLDivElement>(null);
  const div4Ref = useRef<HTMLDivElement>(null);
  const div5Ref = useRef<HTMLDivElement>(null);
  const div6Ref = useRef<HTMLDivElement>(null);
  const div7Ref = useRef<HTMLDivElement>(null);

  return (
    <section
      id="integrations"
      className="relative py-20 sm:py-28 md:py-32 bg-background dark:bg-[#090B0F] overflow-hidden border-b border-border transition-colors duration-300"
    >
      {/* Glow background */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-[#22D3EE]/3 rounded-full blur-[150px] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-16 sm:mb-20 space-y-3 sm:space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117]/80 px-3 py-1 text-xs font-mono font-medium text-primary shadow-sm">
              <Network className="h-3.5 w-3.5" />
              NATIVE INTEGRATIONS
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground font-sans"
          >
            Plug into your{" "}
            <span className="text-primary">existing stack</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-base sm:text-lg text-muted-foreground font-sans leading-relaxed"
          >
            ASEP connects to your developer infrastructure out of the box. No
            rip-and-replace. No vendor lock-in. Just secure, intelligent automation
            over the tools you already use.
          </motion.p>
        </div>

        {/* Two-part layout: animated beam diagram + integration cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* LEFT: Animated beam diagram */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <div
              className="relative flex h-[440px] sm:h-[480px] w-full items-center justify-center overflow-hidden rounded-2xl border border-border/80 dark:border-[#202833] bg-card/40 dark:bg-[#0D1117]/50 backdrop-blur-md p-6 sm:p-8 shadow-sm"
              ref={containerRef}
            >
              {/* Subtle grid background */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,hsl(var(--border)/0.25)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.25)_1px,transparent_1px)] bg-[size:2rem_2rem] opacity-20 pointer-events-none rounded-2xl" />

              <div className="flex size-full flex-col max-w-[280px] max-h-[300px] items-stretch justify-between gap-8">
                {/* Row 1 */}
                <div className="flex flex-row items-center justify-between">
                  <IntegrationNode ref={div1Ref} label="GitHub">
                    <Github className="h-5 w-5 sm:h-6 sm:w-6 text-foreground" />
                  </IntegrationNode>
                  <IntegrationNode ref={div5Ref} label="PostgreSQL">
                    <Database className="h-5 w-5 sm:h-6 sm:w-6 text-[#3B82F6]" />
                  </IntegrationNode>
                </div>

                {/* Row 2 - Center Core */}
                <div className="flex flex-row items-center justify-between">
                  <IntegrationNode ref={div2Ref} label="Docker">
                    <Box className="h-5 w-5 sm:h-6 sm:w-6 text-[#22D3EE]" />
                  </IntegrationNode>
                  <IntegrationNode
                    ref={div4Ref}
                    label="ASEP CORE"
                    glow
                    className="size-14 sm:size-16 border-primary/50 bg-primary/10 shadow-[0_0_30px_rgba(34,211,238,0.3)]"
                  >
                    <Cpu className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
                  </IntegrationNode>
                  <IntegrationNode ref={div6Ref} label="Cloud">
                    <Cloud className="h-5 w-5 sm:h-6 sm:w-6 text-[#A78BFA]" />
                  </IntegrationNode>
                </div>

                {/* Row 3 */}
                <div className="flex flex-row items-center justify-between">
                  <IntegrationNode ref={div3Ref} label="Slack">
                    <Slack className="h-5 w-5 sm:h-6 sm:w-6 text-[#E01E5A]" />
                  </IntegrationNode>
                  <IntegrationNode ref={div7Ref} label="Webhooks">
                    <Webhook className="h-5 w-5 sm:h-6 sm:w-6 text-[#F59E0B]" />
                  </IntegrationNode>
                </div>
              </div>

              {/* Animated Beams to Center */}
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div1Ref}
                toRef={div4Ref}
                curvature={-20}
                gradientStartColor="#22D3EE"
                gradientStopColor="#22D3EE"
                duration={3}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div2Ref}
                toRef={div4Ref}
                gradientStartColor="#22D3EE"
                gradientStopColor="#22D3EE"
                duration={3.5}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div3Ref}
                toRef={div4Ref}
                curvature={20}
                gradientStartColor="#E01E5A"
                gradientStopColor="#22D3EE"
                duration={4}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div5Ref}
                toRef={div4Ref}
                curvature={-20}
                reverse
                gradientStartColor="#3B82F6"
                gradientStopColor="#22D3EE"
                duration={3.2}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div6Ref}
                toRef={div4Ref}
                reverse
                gradientStartColor="#A78BFA"
                gradientStopColor="#22D3EE"
                duration={3.8}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div7Ref}
                toRef={div4Ref}
                curvature={20}
                reverse
                gradientStartColor="#F59E0B"
                gradientStopColor="#22D3EE"
                duration={4.2}
              />
            </div>
          </motion.div>

          {/* RIGHT: Integration cards */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="grid grid-cols-1 sm:grid-cols-2 gap-4"
          >
            {INTEGRATION_CARDS.map((card, i) => (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className={cn(
                  "p-4 rounded-xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] hover:border-primary/40 transition-all duration-200 group flex flex-col justify-between shadow-sm",
                  card.color
                )}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-bold text-foreground font-sans">
                      {card.title}
                    </h3>
                    <div className="flex gap-1">
                      {card.tools.map((tool) => (
                        <span
                          key={tool}
                          className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-muted/60 dark:bg-white/[0.04] text-muted-foreground border border-border/60"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground font-sans leading-relaxed">
                    {card.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
