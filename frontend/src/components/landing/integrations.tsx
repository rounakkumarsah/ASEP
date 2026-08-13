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
            "relative z-10 flex size-14 items-center justify-center rounded-2xl border border-[#202833] bg-[#0D1117] p-3 transition-all duration-300 hover:border-[#22D3EE]/50 hover:scale-110 cursor-pointer group",
            glow &&
              "border-[#22D3EE]/50 bg-[#22D3EE]/5 shadow-[0_0_30px_rgba(34,211,238,0.2)]",
            className
          )}
        >
          {children}
          {glow && (
            <div className="absolute inset-0 rounded-2xl bg-[#22D3EE]/10 animate-pulse" />
          )}
        </div>
        <span className="text-[9px] font-mono font-bold tracking-wider uppercase text-[#667085] group-hover:text-[#9CA6B5]">
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
    color: "border-[#22D3EE]/20 bg-[#22D3EE]/5",
    accent: "text-[#22D3EE]",
  },
  {
    title: "Notifications",
    tools: ["Slack", "Teams", "Email"],
    description: "Real-time governance alerts and execution status updates",
    color: "border-[#2DD4A3]/20 bg-[#2DD4A3]/5",
    accent: "text-[#2DD4A3]",
  },
  {
    title: "Infrastructure",
    tools: ["Docker", "K8s", "VPC"],
    description: "Isolated, resource-limited sandbox environments per task",
    color: "border-[#F5B942]/20 bg-[#F5B942]/5",
    accent: "text-[#F5B942]",
  },
  {
    title: "Cloud Storage",
    tools: ["S3", "GCS", "Azure Blob"],
    description: "Artifact storage, audit logs, and memory persistence layers",
    color: "border-[#38BDF8]/20 bg-[#38BDF8]/5",
    accent: "text-[#38BDF8]",
  },
  {
    title: "Webhooks & APIs",
    tools: ["REST", "GraphQL", "gRPC"],
    description: "Trigger agents from external events and CI/CD pipelines",
    color: "border-[#818CF8]/20 bg-[#818CF8]/5",
    accent: "text-[#818CF8]",
  },
  {
    title: "Databases",
    tools: ["PostgreSQL", "Redis", "Qdrant"],
    description: "Structured state, distributed cache, and semantic memory",
    color: "border-[#FB7185]/20 bg-[#FB7185]/5",
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
      className="relative py-24 sm:py-32 bg-[#090B0F] overflow-hidden border-b border-[#202833]"
    >
      {/* Glow background */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[350px] bg-[#22D3EE]/3 rounded-full blur-[150px] pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4 }}
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-[#202833] bg-[#0D1117]/80 px-3 py-1 text-xs font-mono font-medium text-[#22D3EE]">
              <Network className="h-3.5 w-3.5" />
              NATIVE INTEGRATIONS
            </span>
          </motion.div>

          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-3xl font-extrabold tracking-tight text-[#F5F7FA] sm:text-4xl md:text-5xl font-sans"
          >
            Plug into your{" "}
            <span className="text-[#22D3EE]">existing stack</span>
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-base text-[#9CA6B5] font-sans"
          >
            ASEP connects to your developer infrastructure out of the box. No
            rip-and-replace. No vendor lock-in. Just secure, intelligent automation
            over the tools you already use.
          </motion.p>
        </div>

        {/* Two-part layout: animated beam diagram + integration cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* LEFT: Animated beam diagram */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative"
          >
            <div
              className="relative flex h-[480px] w-full items-center justify-center overflow-hidden rounded-2xl border border-[#202833] bg-[#0D1117]/50 p-8"
              ref={containerRef}
            >
              {/* Subtle grid background */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,#141B26_1px,transparent_1px),linear-gradient(to_bottom,#141B26_1px,transparent_1px)] bg-[size:2rem_2rem] opacity-20 pointer-events-none rounded-2xl" />

              <div className="flex size-full flex-col max-w-[280px] max-h-[300px] items-stretch justify-between gap-8">
                {/* Row 1 */}
                <div className="flex flex-row items-center justify-between">
                  <IntegrationNode ref={div1Ref} label="GitHub">
                    <Github className="h-6 w-6 text-[#F5F7FA]" />
                  </IntegrationNode>
                  <IntegrationNode ref={div5Ref} label="PostgreSQL">
                    <Database className="h-6 w-6 text-[#3B82F6]" />
                  </IntegrationNode>
                </div>

                {/* Row 2 */}
                <div className="flex flex-row items-center justify-between">
                  <IntegrationNode ref={div2Ref} label="Slack">
                    <Slack className="h-6 w-6 text-[#4ADE80]" />
                  </IntegrationNode>

                  {/* Center — ASEP */}
                  <IntegrationNode
                    ref={div4Ref}
                    label="ASEP Core"
                    glow
                    className="!size-20 rounded-3xl"
                  >
                    <Cpu className="h-8 w-8 text-[#22D3EE]" />
                  </IntegrationNode>

                  <IntegrationNode ref={div6Ref} label="Cloud">
                    <Cloud className="h-6 w-6 text-[#38BDF8]" />
                  </IntegrationNode>
                </div>

                {/* Row 3 */}
                <div className="flex flex-row items-center justify-between">
                  <IntegrationNode ref={div3Ref} label="Docker">
                    <Box className="h-6 w-6 text-[#22D3EE]" />
                  </IntegrationNode>
                  <IntegrationNode ref={div7Ref} label="Webhooks">
                    <Webhook className="h-6 w-6 text-[#9CA6B5]" />
                  </IntegrationNode>
                </div>
              </div>

              {/* Animated beams */}
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div1Ref}
                toRef={div4Ref}
                curvature={-60}
                endYOffset={-10}
                pathColor="#202833"
                gradientStartColor="#22D3EE"
                gradientStopColor="#67E8F9"
                duration={3.5}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div2Ref}
                toRef={div4Ref}
                pathColor="#202833"
                gradientStartColor="#22D3EE"
                gradientStopColor="#67E8F9"
                duration={4}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div3Ref}
                toRef={div4Ref}
                curvature={60}
                endYOffset={10}
                pathColor="#202833"
                gradientStartColor="#22D3EE"
                gradientStopColor="#67E8F9"
                duration={3.2}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div5Ref}
                toRef={div4Ref}
                curvature={-60}
                endYOffset={-10}
                reverse
                pathColor="#202833"
                gradientStartColor="#2DD4A3"
                gradientStopColor="#22D3EE"
                duration={4.2}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div6Ref}
                toRef={div4Ref}
                reverse
                pathColor="#202833"
                gradientStartColor="#38BDF8"
                gradientStopColor="#22D3EE"
                duration={3.8}
              />
              <AnimatedBeam
                containerRef={containerRef}
                fromRef={div7Ref}
                toRef={div4Ref}
                curvature={60}
                endYOffset={10}
                reverse
                pathColor="#202833"
                gradientStartColor="#818CF8"
                gradientStopColor="#22D3EE"
                duration={4.5}
              />

              {/* Bottom label */}
              <div className="absolute bottom-4 left-0 right-0 flex justify-center">
                <span className="text-[10px] font-mono text-[#667085] bg-[#0D1117] px-3 py-1 rounded-full border border-[#202833]">
                  MCP Unified Data Bus — bidirectional
                </span>
              </div>
            </div>
          </motion.div>

          {/* RIGHT: Integration cards grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {INTEGRATION_CARDS.map((card, i) => (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className={`relative p-5 rounded-xl border ${card.color} backdrop-blur-sm hover:scale-[1.02] transition-all duration-300 cursor-default group`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className={`text-xs font-mono font-bold uppercase tracking-wider ${card.accent}`}>
                      {card.title}
                    </h3>
                    <div className="flex gap-1">
                      {card.tools.slice(0, 3).map((tool) => (
                        <span
                          key={tool}
                          className="text-[9px] font-mono bg-[#090B0F] border border-[#202833] px-1.5 py-0.5 rounded text-[#667085]"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="text-[11px] text-[#9CA6B5] leading-relaxed font-sans">
                    {card.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Bottom CTA strip */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="mt-16 flex flex-col sm:flex-row items-center justify-center gap-4 text-center"
        >
          <p className="text-sm text-[#9CA6B5] font-sans">
            Don&apos;t see your tool?{" "}
            <span className="text-[#22D3EE] font-medium">
              Any MCP-compatible server connects instantly.
            </span>
          </p>
        </motion.div>
      </div>
    </section>
  );
}
