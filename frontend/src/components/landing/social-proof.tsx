"use client";

import { motion, useInView, animate } from "framer-motion";
import { useEffect, useRef } from "react";
import { Quote, Star, Building } from "lucide-react";
import Marquee from "@/components/ui/marquee";

const TECHNOLOGIES = [
  { name: "FastAPI", color: "#14B8A6" },
  { name: "PostgreSQL", color: "#3B82F6" },
  { name: "Redis", color: "#EF4444" },
  { name: "Docker", color: "#2563EB" },
  { name: "LangGraph", color: "#22D3EE" },
  { name: "Qdrant", color: "#A855F7" },
  { name: "Neo4j", color: "#0D9488" },
  { name: "Python", color: "#EAB308" },
  { name: "Next.js", color: "#67E8F9" },
];

const METRICS = [
  { value: 6, label: "Core Agents", prefix: "", suffix: "", decimals: 0 },
  { value: 3, label: "Memory Layers", prefix: "", suffix: "", decimals: 0 },
  { value: 99.98, label: "Uptime", prefix: "", suffix: "%", decimals: 2 },
  { value: 15, label: "Latency", prefix: "<", suffix: "ms", decimals: 0 },
  { value: 5, label: "Governance Policies", prefix: "", suffix: "+", decimals: 0 },
  { value: 0, label: "Data Breaches", prefix: "", suffix: "", decimals: 0 },
];

const TESTIMONIALS_ROW1 = [
  {
    quote: "ASEP fundamentally shifted our approach to multi-agent architectures. We no longer worry about local orchestration bottlenecks.",
    name: "Sarah Chen",
    title: "VP of Engineering, CloudCorp",
    avatar: "SC",
    color: "from-[#22D3EE] to-blue-500",
  },
  {
    quote: "Having a unified control plane for sandboxed local execution is exactly what enterprise AI needs to meet compliance.",
    name: "Elena Rostova",
    title: "CTO, Apex Data",
    avatar: "ER",
    color: "from-[#2DD4A3] to-emerald-600",
  },
  {
    quote: "Deploying local LLMs in secure sandboxes with cryptographic human-in-the-loop policies is standardizing our agent deployments.",
    name: "David K.",
    title: "Principal AI Engineer, ScaleCorp",
    avatar: "DK",
    color: "from-blue-400 to-cyan-500",
  },
];

const TESTIMONIALS_ROW2 = [
  {
    quote: "The governance and memory layer abstraction saves our infrastructure team thousands of hours. It just works out of the box.",
    name: "Michael Torres",
    title: "Lead AI Architect, Nexus Labs",
    avatar: "MT",
    color: "from-emerald-400 to-teal-500",
  },
  {
    quote: "The integration of Model Context Protocol (MCP) tool registry is seamless. Speed, compliance, and memory in one tool.",
    name: "Maya Lin",
    title: "CTO, Quantum Systems",
    avatar: "ML",
    color: "from-cyan-400 to-teal-400",
  },
  {
    quote: "We replaced our complex orchestration scripts with ASEP. 90% reduction in agent failure recovery time.",
    name: "James Wright",
    title: "Lead Developer, BlueOrigin Labs",
    avatar: "JW",
    color: "from-[#22D3EE] to-[#2DD4A3]",
  },
];

function Counter({ from = 0, to, decimals = 0, suffix = "", prefix = "" }: { from?: number; to: number; decimals?: number; suffix?: string; prefix?: string }) {
  const nodeRef = useRef<HTMLSpanElement>(null);
  const inView = useInView(nodeRef, { once: true, margin: "-100px" });
  
  useEffect(() => {
    const node = nodeRef.current;
    if (!node || !inView) return;
    const controls = animate(from, to, {
      duration: 2,
      ease: "easeOut",
      onUpdate(value) {
        node.textContent = `${prefix}${value.toFixed(decimals)}${suffix}`;
      },
    });
    return () => controls.stop();
  }, [from, to, decimals, prefix, suffix, inView]);
  
  return <span ref={nodeRef} className="tabular-nums tracking-tight">{prefix}{from.toFixed(decimals)}{suffix}</span>;
}

export function SocialProofSection() {
  return (
    <section className="relative overflow-hidden bg-background dark:bg-[#090B0F] py-20 sm:py-28 md:py-32 border-b border-border transition-colors duration-300">
      {/* Background elements */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-[#22D3EE]/5 rounded-full blur-[120px] pointer-events-none" />

      {/* TOP: Technology Marquee */}
      <div className="flex flex-col items-center space-y-6 sm:space-y-8 mb-20 sm:mb-28 z-10 relative">
        <span className="text-xs font-mono font-medium text-muted-foreground tracking-[0.2em] uppercase">Trusted Stack</span>
        <div className="relative w-full overflow-hidden flex flex-col items-center">
          <div className="pointer-events-none absolute inset-y-0 left-0 w-24 sm:w-32 bg-gradient-to-r from-background z-10" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-24 sm:w-32 bg-gradient-to-l from-background z-10" />
          <Marquee className="[--duration:40s]" pauseOnHover>
            {TECHNOLOGIES.map((tech) => (
              <div 
                key={tech.name} 
                className="flex items-center space-x-3 px-5 sm:px-6 py-2.5 sm:py-3 mx-2.5 sm:mx-3 rounded-full border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] hover:bg-accent hover:border-primary/40 transition-all cursor-default shadow-sm"
              >
                <div 
                  className="w-2.5 h-2.5 rounded-full shadow-[0_0_8px_currentColor]" 
                  style={{ backgroundColor: tech.color, color: tech.color }} 
                />
                <span className="font-semibold tracking-wide text-sm text-foreground">{tech.name}</span>
              </div>
            ))}
          </Marquee>
        </div>
      </div>

      <div className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-[1fr_1.5fr] gap-12 lg:gap-12 items-center">
          
          {/* LEFT: Metrics Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="flex flex-col space-y-8 sm:space-y-10"
          >
            <div className="space-y-3 sm:space-y-4 text-center lg:text-left">
              <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground leading-tight">
                Engineered for <br className="hidden sm:block"/>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#22D3EE] to-[#2DD4A3]">Production Autonomy</span>
              </h2>
              <p className="text-base text-muted-foreground leading-relaxed max-w-md mx-auto lg:mx-0">
                ASEP replaces brittle pipelines with a secure, hardened runtime architecture designed for mission-critical enterprise deployments.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 gap-x-6 sm:gap-x-8 gap-y-8 sm:gap-y-10">
              {METRICS.map((metric, idx) => (
                <motion.div 
                  key={metric.label}
                  initial={{ opacity: 0, y: 15 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: idx * 0.08 }}
                  className="space-y-1.5 relative pl-3 sm:pl-4"
                >
                  {/* Decorative line */}
                  <div className="absolute left-0 top-1 bottom-1 w-[2px] bg-gradient-to-b from-[#22D3EE]/60 to-transparent rounded-full" />
                  
                  <div className="text-3xl sm:text-4xl font-extrabold text-foreground tracking-tight">
                    <Counter 
                      to={metric.value} 
                      decimals={metric.decimals} 
                      prefix={metric.prefix} 
                      suffix={metric.suffix} 
                    />
                  </div>
                  <div className="text-[11px] sm:text-xs font-mono uppercase tracking-wider text-muted-foreground">
                    {metric.label}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* RIGHT: Testimonial Wall */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="relative overflow-hidden -mx-4 sm:mx-0 py-4"
          >
            {/* Fade overlays for the marquee borders */}
            <div className="pointer-events-none absolute inset-y-0 left-0 w-16 sm:w-24 bg-gradient-to-r from-background z-10" />
            <div className="pointer-events-none absolute inset-y-0 right-0 w-16 sm:w-24 bg-gradient-to-l from-background z-10" />

            <div className="flex flex-col gap-6">
              {/* Marquee Row 1 */}
              <Marquee pauseOnHover className="[--duration:40s]">
                {TESTIMONIALS_ROW1.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col justify-between w-[300px] sm:w-[380px] p-6 sm:p-8 rounded-3xl border border-border/80 dark:border-[#202833] bg-card/90 dark:bg-[#0D1117]/80 backdrop-blur-xl hover:border-primary/40 hover:bg-accent/40 transition-all duration-300 mx-3 group shadow-sm"
                  >
                    <div className="flex justify-between items-start mb-5 sm:mb-6">
                      <div className="flex items-center gap-1 text-amber-400">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} className="h-4 w-4 fill-current" />
                        ))}
                      </div>
                      <Quote className="h-8 w-8 sm:h-10 sm:w-10 text-muted-foreground/30 group-hover:text-primary/30 transition-colors" />
                    </div>
                    
                    <p className="text-sm leading-relaxed text-foreground mb-6 sm:mb-8 font-medium">
                      &ldquo;{item.quote}&rdquo;
                    </p>
                    
                    <div className="flex items-center gap-3.5 mt-auto">
                      <div className={`h-11 w-11 rounded-full bg-gradient-to-br ${item.color} p-[2px]`}>
                        <div className="h-full w-full rounded-full bg-background dark:bg-[#090B0F] flex items-center justify-center">
                          <span className={`text-xs font-bold bg-clip-text text-transparent bg-gradient-to-br ${item.color}`}>
                            {item.avatar}
                          </span>
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-bold text-foreground">{item.name}</h4>
                        <p className="text-xs text-muted-foreground mt-0.5">{item.title}</p>
                      </div>
                      <Building className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </Marquee>

              {/* Marquee Row 2 */}
              <Marquee reverse pauseOnHover className="[--duration:40s]">
                {TESTIMONIALS_ROW2.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col justify-between w-[300px] sm:w-[380px] p-6 sm:p-8 rounded-3xl border border-border/80 dark:border-[#202833] bg-card/90 dark:bg-[#0D1117]/80 backdrop-blur-xl hover:border-primary/40 hover:bg-accent/40 transition-all duration-300 mx-3 group shadow-sm"
                  >
                    <div className="flex justify-between items-start mb-5 sm:mb-6">
                      <div className="flex items-center gap-1 text-amber-400">
                        {[...Array(5)].map((_, i) => (
                          <Star key={i} className="h-4 w-4 fill-current" />
                        ))}
                      </div>
                      <Quote className="h-8 w-8 sm:h-10 sm:w-10 text-muted-foreground/30 group-hover:text-primary/30 transition-colors" />
                    </div>
                    
                    <p className="text-sm leading-relaxed text-foreground mb-6 sm:mb-8 font-medium">
                      &ldquo;{item.quote}&rdquo;
                    </p>
                    
                    <div className="flex items-center gap-3.5 mt-auto">
                      <div className={`h-11 w-11 rounded-full bg-gradient-to-br ${item.color} p-[2px]`}>
                        <div className="h-full w-full rounded-full bg-background dark:bg-[#090B0F] flex items-center justify-center">
                          <span className={`text-xs font-bold bg-clip-text text-transparent bg-gradient-to-br ${item.color}`}>
                            {item.avatar}
                          </span>
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="text-sm font-bold text-foreground">{item.name}</h4>
                        <p className="text-xs text-muted-foreground mt-0.5">{item.title}</p>
                      </div>
                      <Building className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                    </div>
                  </div>
                ))}
              </Marquee>
            </div>
          </motion.div>
          
        </div>
      </div>
    </section>
  );
}
