'use client';

import { motion } from 'framer-motion';
import { BrainCircuit, Terminal, Layers, ShieldCheck, CheckCircle, LayoutDashboard, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

const fadeUpVariant = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

function AutonomousPlanningVisual() {
  return (
    <div className="relative w-full h-40 flex items-center justify-center overflow-hidden bg-card/60 dark:bg-[#090B0F]/50 rounded-xl border border-border/80 dark:border-[#202833] mt-6">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.08)_0%,transparent_70%)]" />
      <div className="flex items-center gap-4 sm:gap-6">
        {/* Node 1 */}
        <motion.div 
          animate={{ boxShadow: ['0 0 0 0 rgba(34,211,238,0)', '0 0 20px 2px rgba(34,211,238,0.5)', '0 0 0 0 rgba(34,211,238,0)'] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="w-11 h-11 rounded-xl bg-background dark:bg-[#0D1117] border border-[#22D3EE]/40 flex items-center justify-center z-10 shadow-lg"
        >
          <div className="w-3 h-3 rounded-full bg-[#22D3EE]" />
        </motion.div>
        
        {/* Line */}
        <div className="w-14 sm:w-20 h-[2px] bg-border dark:bg-[#202833] relative overflow-hidden">
          <motion.div 
            initial={{ x: '-100%' }}
            animate={{ x: '100%' }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="absolute inset-0 bg-gradient-to-r from-transparent via-[#22D3EE] to-transparent"
          />
        </div>

        {/* Node 2 & 3 */}
        <div className="flex flex-col gap-3">
          <motion.div 
            animate={{ boxShadow: ['0 0 0 0 rgba(34,211,238,0)', '0 0 15px 2px rgba(34,211,238,0.4)', '0 0 0 0 rgba(34,211,238,0)'] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
            className="w-9 h-9 rounded-xl bg-background dark:bg-[#0D1117] border border-[#22D3EE]/40 flex items-center justify-center z-10"
          >
            <div className="w-2.5 h-2.5 rounded-full bg-[#22D3EE]" />
          </motion.div>
          <motion.div 
            animate={{ boxShadow: ['0 0 0 0 rgba(45,212,163,0)', '0 0 15px 2px rgba(45,212,163,0.4)', '0 0 0 0 rgba(45,212,163,0)'] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="w-9 h-9 rounded-xl bg-background dark:bg-[#0D1117] border border-[#2DD4A3]/40 flex items-center justify-center z-10"
          >
            <div className="w-2.5 h-2.5 rounded-full bg-[#2DD4A3]" />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function TerminalVisual() {
  const [text, setText] = useState('');
  const fullText = '> asep run --mode isolated\n[INFO] Initializing sandbox...\n[SUCCESS] Environment ready.';
  
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setText(fullText.slice(0, i));
      i++;
      if (i > fullText.length) {
        setTimeout(() => { i = 0; }, 3000);
      }
    }, 50);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full h-40 bg-card dark:bg-[#090B0F] rounded-xl border border-border/80 dark:border-[#202833] overflow-hidden flex flex-col font-mono text-xs mt-6">
      <div className="h-6 w-full border-b border-border/80 dark:border-[#202833] bg-muted/40 dark:bg-[#0D1117] flex items-center px-3 gap-1.5">
        <div className="w-2 h-2 rounded-full bg-red-500/60" />
        <div className="w-2 h-2 rounded-full bg-yellow-500/60" />
        <div className="w-2 h-2 rounded-full bg-green-500/60" />
      </div>
      <div className="p-3.5 text-muted-foreground whitespace-pre-wrap flex-1 flex flex-col leading-relaxed">
        <span>{text}<motion.span animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.8 }}>|</motion.span></span>
      </div>
    </div>
  );
}

function LayersVisual() {
  return (
    <div className="w-full h-40 flex items-center justify-center relative mt-6" style={{ perspective: '1000px' }}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          animate={{ 
            y: [0, -6, 0],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            delay: i * 0.2,
            ease: "easeInOut"
          }}
          className={cn(
            "absolute w-40 h-20 rounded-xl border border-border/80 dark:border-[#202833] backdrop-blur-md flex items-center justify-center transition-colors shadow-lg",
            i === 0 && "bg-card/90 dark:bg-[#0D1117]/90 -translate-y-6 z-30 border-[#22D3EE]/40",
            i === 1 && "bg-card/75 dark:bg-[#0D1117]/80 z-20",
            i === 2 && "bg-card/60 dark:bg-[#0D1117]/70 translate-y-6 z-10"
          )}
          style={{
            transform: `rotateX(60deg) rotateZ(-45deg) translateZ(${i * 20}px)`
          }}
        >
          <div className="w-2 h-2 rounded-full bg-[#22D3EE]/80" />
        </motion.div>
      ))}
    </div>
  );
}

function GovernanceVisual() {
  return (
    <div className="w-full h-40 bg-card/60 dark:bg-[#090B0F] border border-border/80 dark:border-[#202833] rounded-xl p-4 flex flex-col justify-between mt-6">
      <div className="flex justify-between items-center text-xs">
        <span className="font-mono text-muted-foreground flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          HITL APPROVAL
        </span>
        <span className="text-[10px] font-mono bg-muted/60 dark:bg-[#111720] border border-border/60 text-muted-foreground px-2 py-0.5 rounded">
          Gate #492
        </span>
      </div>
      
      <div className="p-2.5 rounded-lg bg-background dark:bg-[#0D1117] border border-border/60 dark:border-[#202833] text-xs font-mono">
        <div className="text-foreground truncate font-semibold">PR #142: Deploy auth schema</div>
        <div className="text-[10px] text-muted-foreground mt-0.5">Signed: SHA256-e48f</div>
      </div>

      <div className="flex gap-2">
        <div className="flex-1 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[11px] font-mono font-bold flex items-center justify-center gap-1">
          <Check className="w-3 h-3" /> Approve
        </div>
        <div className="flex-1 py-1.5 rounded-lg bg-muted/60 border border-border text-muted-foreground text-[11px] font-mono flex items-center justify-center">
          Reject
        </div>
      </div>
    </div>
  );
}

function EvaluationVisual() {
  return (
    <div className="w-full h-40 bg-card/60 dark:bg-[#090B0F] border border-border/80 dark:border-[#202833] rounded-xl p-4 flex flex-col justify-center items-center relative overflow-hidden mt-6">
      <div className="relative flex items-center justify-center">
        <svg className="w-24 h-24 transform -rotate-90">
          <circle
            cx="48"
            cy="48"
            r="38"
            stroke="currentColor"
            strokeWidth="6"
            className="text-border dark:text-[#202833]"
            fill="transparent"
          />
          <motion.circle
            cx="48"
            cy="48"
            r="38"
            stroke="#2DD4A3"
            strokeWidth="6"
            strokeDasharray={2 * Math.PI * 38}
            initial={{ strokeDashoffset: 2 * Math.PI * 38 }}
            whileInView={{ strokeDashoffset: 2 * Math.PI * 38 * (1 - 0.98) }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            strokeLinecap="round"
            fill="transparent"
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-xl font-bold font-mono text-foreground">98%</span>
          <span className="text-[8px] font-mono text-muted-foreground">SCORE</span>
        </div>
      </div>
    </div>
  );
}

function ControlPlaneVisual() {
  return (
    <div className="w-full h-40 bg-card/60 dark:bg-[#090B0F] border border-border/80 dark:border-[#202833] rounded-xl p-4 flex flex-col justify-end relative overflow-hidden mt-6">
      <div className="absolute top-0 right-0 p-4 flex gap-1.5">
        <div className="w-1.5 h-3 bg-[#22D3EE] rounded-sm animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
        <div className="w-1.5 h-4 bg-[#22D3EE]/70 rounded-sm animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.3)]" style={{ animationDelay: '0.2s' }} />
        <div className="w-1.5 h-2 bg-[#22D3EE]/40 rounded-sm animate-pulse" style={{ animationDelay: '0.4s' }} />
      </div>
      <div className="absolute top-4 left-4 text-[10px] font-mono text-muted-foreground">ACTIVE METRICS</div>
      <div className="flex justify-between items-end gap-2 h-20 w-full mt-4">
        {[40, 70, 45, 90, 60, 80, 50, 65].map((h, i) => (
          <motion.div 
            key={i}
            initial={{ height: 0 }}
            whileInView={{ height: `${h}%` }}
            transition={{ duration: 0.6, delay: i * 0.05, type: "spring", stiffness: 100 }}
            className="flex-1 bg-gradient-to-t from-[#22D3EE]/10 to-[#22D3EE]/40 rounded-t-sm border-t border-[#22D3EE]/60"
          />
        ))}
      </div>
    </div>
  );
}

export function FeaturesSection() {
  const features = [
    {
      title: 'Autonomous Planning',
      description: 'Intelligent breakdown of complex goals into directed acyclic graphs of executable tasks with dependency resolution.',
      icon: <BrainCircuit className="w-6 h-6 text-[#22D3EE]" />,
      accentClass: 'group-hover:border-[#22D3EE]/50 group-hover:shadow-[0_0_30px_-5px_rgba(34,211,238,0.15)]',
      span: 'md:col-span-4',
      visual: <AutonomousPlanningVisual />
    },
    {
      title: 'Isolated Execution',
      description: 'Secure, sandboxed environments for code generation and arbitrary execution without polluting host systems.',
      icon: <Terminal className="w-6 h-6 text-[#22D3EE]" />,
      accentClass: 'group-hover:border-[#22D3EE]/50 group-hover:shadow-[0_0_30px_-5px_rgba(34,211,238,0.15)]',
      span: 'md:col-span-2',
      visual: <TerminalVisual />
    },
    {
      title: 'Multi-Layer Memory',
      description: 'Short-term context windows combined with long-term vector storage for persistent agent recall.',
      icon: <Layers className="w-6 h-6 text-[#22D3EE]" />,
      accentClass: 'group-hover:border-[#22D3EE]/50 group-hover:shadow-[0_0_30px_-5px_rgba(34,211,238,0.15)]',
      span: 'md:col-span-2',
      visual: <LayersVisual />
    },
    {
      title: 'Governance & HITL',
      description: 'Enterprise-grade Human-in-the-Loop approval workflows for high-stakes actions and unverified state transitions.',
      icon: <ShieldCheck className="w-6 h-6 text-[#2DD4A3]" />,
      accentClass: 'group-hover:border-[#2DD4A3]/50 group-hover:shadow-[0_0_30px_-5px_rgba(45,212,163,0.15)]',
      span: 'md:col-span-4',
      visual: <GovernanceVisual />
    },
    {
      title: 'Real-time Evaluation',
      description: 'Continuous validation scoring mechanisms to ensure agent outputs align with desired objectives.',
      icon: <CheckCircle className="w-6 h-6 text-[#2DD4A3]" />,
      accentClass: 'group-hover:border-[#2DD4A3]/50 group-hover:shadow-[0_0_30px_-5px_rgba(45,212,163,0.15)]',
      span: 'md:col-span-3',
      visual: <EvaluationVisual />
    },
    {
      title: 'Control Plane',
      description: 'Centralized observability dashboards for tracing executions, token usage, and subagent telemetry.',
      icon: <LayoutDashboard className="w-6 h-6 text-[#22D3EE]" />,
      accentClass: 'group-hover:border-[#22D3EE]/50 group-hover:shadow-[0_0_30px_-5px_rgba(34,211,238,0.15)]',
      span: 'md:col-span-3',
      visual: <ControlPlaneVisual />
    }
  ];

  return (
    <section className="py-20 sm:py-28 md:py-32 bg-background dark:bg-[#090B0F] border-b border-border relative overflow-hidden transition-colors duration-300">
      {/* Background elements */}
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
      <div className="absolute top-[-20%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[#22D3EE]/5 blur-[120px] pointer-events-none" />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUpVariant}
          className="text-center max-w-3xl mx-auto mb-16 sm:mb-20"
        >
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold text-foreground tracking-tight mb-4 sm:mb-6">
            Architected for <span className="relative whitespace-nowrap">
              Scale
              <span className="absolute -bottom-2 left-0 w-full h-1 bg-gradient-to-r from-[#22D3EE] to-[#2DD4A3] rounded-full" />
            </span>
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            Everything you need to orchestrate complex AI workflows. Built on a foundation of reliability, security, and uncompromising performance.
          </p>
        </motion.div>

        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={staggerContainer}
          className="grid grid-cols-1 md:grid-cols-6 gap-6"
        >
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              variants={fadeUpVariant}
              className={cn(
                "group relative bg-card dark:bg-[#0D1117] rounded-2xl border border-border/80 dark:border-[#202833] p-6 flex flex-col justify-between transition-all duration-300 overflow-hidden shadow-sm hover:shadow-md",
                feature.span,
                feature.accentClass
              )}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.03] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              
              <div className="relative z-10">
                <div className="flex items-center gap-3.5 mb-3.5">
                  <motion.div 
                    className="p-2.5 rounded-xl bg-muted/60 dark:bg-[#111720] border border-border/80 dark:border-[#202833] group-hover:border-transparent transition-colors"
                    whileHover={{ y: -2 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    {feature.icon}
                  </motion.div>
                  <h3 className="text-lg sm:text-xl font-semibold text-foreground">{feature.title}</h3>
                </div>
                <p className="text-muted-foreground leading-relaxed text-sm">
                  {feature.description}
                </p>
              </div>

              <div className="relative z-10 w-full">
                {feature.visual}
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
