"use client";

import { motion, Variants } from "framer-motion";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Github, Terminal, Cpu } from "lucide-react";

export function HeroSection() {
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: "easeOut" },
    },
  };

  return (
    <section className="relative overflow-hidden bg-[#090B0F] pt-24 pb-32 md:pt-32 md:pb-40 border-b border-[#202833]">
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Badge */}
          <motion.div
            variants={itemVariants}
            className="mb-8 flex justify-center"
          >
            <span className="inline-flex items-center rounded-md border border-[#202833] bg-[#0D1117] px-3 py-1 text-xs font-mono font-medium text-[#22D3EE] shadow-xs">
              <span className="mr-2 flex h-1.5 w-1.5 rounded-full bg-[#2DD4A3] animate-pulse" />
              v0.1.0 • Autonomous Software Engineering Platform
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={itemVariants}
            className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight text-[#F5F7FA] sm:text-5xl md:text-6xl lg:text-7xl font-sans"
          >
            Autonomous Software Engineering at Enterprise Scale
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            variants={itemVariants}
            className="mx-auto mt-6 max-w-2xl text-base leading-relaxed text-[#9CA6B5] sm:text-lg font-sans"
          >
            Unify Planning, Execution, Memory, and Governance. ASEP is the production-grade control plane for autonomous software agents built for absolute reliability and scale.
          </motion.p>

          {/* CTAs */}
          <motion.div
            variants={itemVariants}
            className="mt-10 flex flex-col items-center justify-center space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0"
          >
            <Link href="/signup">
              <Button size="lg" className="h-11 px-6 text-sm font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] group">
                <span>Deploy Control Plane</span>
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank">
              <Button
                size="lg"
                variant="outline"
                className="h-11 px-6 text-sm font-mono font-medium border-[#202833] bg-[#0D1117] text-[#F5F7FA] hover:bg-[#111720]"
              >
                <Github className="mr-2 h-4 w-4" />
                View Source
              </Button>
            </Link>
          </motion.div>
        </motion.div>

        {/* Control Plane Visual Mockup */}
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
          className="mx-auto mt-16 max-w-5xl"
        >
          <div className="relative rounded-xl border border-[#202833] bg-[#0D1117] p-2 shadow-xl">
            <div className="flex h-[380px] sm:h-[450px] w-full flex-col overflow-hidden rounded-lg border border-[#202833] bg-[#090B0F] md:flex-row font-mono text-xs">
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
              <div className="flex-1 p-6 space-y-4">
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
                <div className="h-36 w-full rounded-lg border border-[#202833] bg-[#0D1117] p-4 flex flex-col justify-center items-center text-[#667085]">
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
