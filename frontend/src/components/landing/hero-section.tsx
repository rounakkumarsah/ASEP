"use client";

import { motion, Variants } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Github, Terminal, Cpu } from "lucide-react";
import { Globe } from "@/components/ui/globe";

export function HeroSection() {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 15 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, ease: "easeOut" },
    },
  };

  return (
    <section className="relative overflow-hidden bg-[#090B0F] pt-28 pb-24 border-b border-[#202833]">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Headline and CTAs */}
          <div className="lg:col-span-7 text-left space-y-6">
            <motion.div
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-6"
            >
              {/* Badge */}
              <motion.div variants={itemVariants} className="flex">
                <span className="inline-flex items-center rounded-md border border-[#202833] bg-[#0D1117] px-3 py-1 text-xs font-mono font-medium text-[#22D3EE] shadow-sm">
                  <span className="mr-2 flex h-1.5 w-1.5 rounded-full bg-[#2DD4A3] animate-pulse" />
                  v0.1.0 • Autonomous Software Engineering Platform
                </span>
              </motion.div>

              {/* Headline */}
              <motion.h1
                variants={itemVariants}
                className="text-4xl font-extrabold tracking-tight text-[#F5F7FA] sm:text-5xl md:text-6xl font-sans leading-[1.1]"
              >
                Build Enterprise AI Software with Autonomous Engineering Agents
              </motion.h1>

              {/* Subheadline */}
              <motion.p
                variants={itemVariants}
                className="max-w-2xl text-sm leading-relaxed text-[#9CA6B5] sm:text-base font-sans"
              >
                Unify Planning, Execution, Memory, and Governance. ASEP is the production-grade control plane for autonomous software agents built for absolute reliability and scale.
              </motion.p>

              {/* CTAs */}
              <motion.div
                variants={itemVariants}
                className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2"
              >
                <Link href="/signup">
                  <Button size="lg" className="h-11 px-6 text-sm font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] group w-full sm:w-auto">
                    <span>Deploy Control Plane</span>
                    <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
                <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank">
                  <Button
                    size="lg"
                    variant="outline"
                    className="h-11 px-6 text-sm font-mono font-medium border-[#202833] bg-[#0D1117] text-[#F5F7FA] hover:bg-[#111720] w-full sm:w-auto"
                  >
                    <Github className="mr-2 h-4 w-4" />
                    View Source
                  </Button>
                </Link>
              </motion.div>

              {/* Logo Cloud & Trust Indicators */}
              <motion.div variants={itemVariants} className="pt-8 border-t border-[#202833]/60 space-y-3">
                <span className="text-[10px] font-mono text-[#667085] uppercase tracking-wider block">TRUSTED BY INNOVATION TEAMS AT</span>
                <div className="flex flex-wrap items-center gap-x-8 gap-y-4 opacity-55 hover:opacity-80 transition-opacity duration-300">
                  <span className="font-mono font-bold tracking-widest text-[#9CA6B5] text-sm">CLOUD CORP</span>
                  <span className="font-mono font-bold tracking-widest text-[#9CA6B5] text-sm">NEXUS LABS</span>
                  <span className="font-mono font-bold tracking-widest text-[#9CA6B5] text-sm">APEX DATA</span>
                  <span className="font-mono font-bold tracking-widest text-[#9CA6B5] text-sm">SANDBOX INC</span>
                </div>
              </motion.div>
            </motion.div>
          </div>

          {/* Right Column: WebGL Interactive Globe */}
          <div className="lg:col-span-5 flex justify-center items-center relative">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,#111720_0%,transparent_70%)] opacity-50" />
            <div className="relative border border-[#202833] bg-[#0D1117] rounded-full p-6 shadow-2xl flex items-center justify-center max-w-[420px] w-full aspect-square">
              <div className="absolute inset-0 border border-dashed border-[#202833]/60 rounded-full animate-[spin_120s_linear_infinite]" />
              <Globe />
            </div>
          </div>
        </div>

        {/* Control Plane Visual Mockup */}
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.99 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.3, ease: "easeOut" }}
          className="mx-auto mt-20 max-w-5xl"
        >
          <div className="relative rounded-xl border border-[#202833] bg-[#0D1117] p-2 shadow-xl">
            <div className="flex h-[360px] sm:h-[420px] w-full flex-col overflow-hidden rounded-lg border border-[#202833] bg-[#090B0F] md:flex-row font-mono text-xs">
              {/* Mock Sidebar */}
              <div className="hidden w-52 border-r border-[#202833] bg-[#0D1117] p-4 md:block space-y-4">
                <div className="flex items-center space-x-2 text-[#22D3EE] font-bold">
                  <Cpu className="h-4 w-4" />
                  <span>ASEP CONTROL</span>
                </div>
                <div className="space-y-1">
                  {["Overview", "Projects", "Playground", "Evaluation", "Settings"].map((item, idx) => (
                    <div key={item} className={`px-2.5 py-1.5 rounded flex items-center justify-between ${idx === 0 ? "bg-[#111720] text-[#F5F7FA] border-l-2 border-[#22D3EE]" : "text-[#667085]"}`}>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
              {/* Mock Main Area */}
              <div className="flex-1 p-6 space-y-4 overflow-hidden">
                <div className="flex items-center justify-between border-b border-[#202833] pb-3">
                  <div className="flex items-center space-x-2 text-[#F5F7FA] font-bold">
                    <Terminal className="h-4 w-4 text-[#22D3EE]" />
                    <span>System Telemetry</span>
                  </div>
                  <span className="text-[10px] text-[#2DD4A3] bg-[#2DD4A3]/10 px-2 py-0.5 rounded border border-[#2DD4A3]/20">STATUS: OPERATIONAL</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {[
                    { label: "CPU Load", val: "14%" },
                    { label: "Memory", val: "38%" },
                    { label: "Active Agents", val: "6" },
                  ].map((stat) => (
                    <div key={stat.label} className="p-3 rounded-lg border border-[#202833] bg-[#0D1117]">
                      <span className="text-[10px] text-[#667085] uppercase block">{stat.label}</span>
                      <span className="text-lg font-bold text-[#F5F7FA] mt-1 block">{stat.val}</span>
                    </div>
                  ))}
                </div>
                <div className="h-32 w-full rounded-lg border border-[#202833] bg-[#0D1117] p-4 flex flex-col justify-center items-center text-[#667085]">
                  <span>Execution Stream Idle • Ready for Orchestration</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
