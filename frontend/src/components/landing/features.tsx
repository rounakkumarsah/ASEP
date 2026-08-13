'use client'

import { motion } from 'framer-motion'
import { BrainCircuit, Terminal, Layers, ShieldCheck, CheckCircle, LayoutDashboard, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEffect, useState } from 'react'

const fadeUpVariant = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } }
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
}

function AutonomousPlanningVisual() {
  return (
    <div className="relative w-full h-40 flex items-center justify-center overflow-hidden bg-[#090B0F]/50 rounded-lg border border-[#202833] mt-6">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(34,211,238,0.05)_0%,transparent_70%)]" />
      <div className="flex items-center gap-6">
        {/* Node 1 */}
        <motion.div 
          animate={{ boxShadow: ['0 0 0 0 rgba(34,211,238,0)', '0 0 20px 2px rgba(34,211,238,0.5)', '0 0 0 0 rgba(34,211,238,0)'] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="w-12 h-12 rounded-xl bg-[#0D1117] border border-[#22D3EE]/30 flex items-center justify-center z-10 shadow-lg"
        >
          <div className="w-3 h-3 rounded-full bg-[#22D3EE]" />
        </motion.div>
        
        {/* Line */}
        <div className="w-20 h-[2px] bg-[#202833] relative overflow-hidden">
          <motion.div 
            initial={{ x: '-100%' }}
            animate={{ x: '100%' }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="absolute inset-0 bg-gradient-to-r from-transparent via-[#22D3EE] to-transparent"
          />
        </div>

        {/* Node 2 & 3 */}
        <div className="flex flex-col gap-4">
          <motion.div 
            animate={{ boxShadow: ['0 0 0 0 rgba(34,211,238,0)', '0 0 15px 2px rgba(34,211,238,0.4)', '0 0 0 0 rgba(34,211,238,0)'] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
            className="w-10 h-10 rounded-xl bg-[#0D1117] border border-[#22D3EE]/30 flex items-center justify-center z-10"
          >
            <div className="w-2.5 h-2.5 rounded-full bg-[#22D3EE]" />
          </motion.div>
          <motion.div 
            animate={{ boxShadow: ['0 0 0 0 rgba(45,212,163,0)', '0 0 15px 2px rgba(45,212,163,0.4)', '0 0 0 0 rgba(45,212,163,0)'] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="w-10 h-10 rounded-xl bg-[#0D1117] border border-[#2DD4A3]/30 flex items-center justify-center z-10"
          >
            <div className="w-2.5 h-2.5 rounded-full bg-[#2DD4A3]" />
          </motion.div>
        </div>
      </div>
    </div>
  )
}

function TerminalVisual() {
  const [text, setText] = useState('')
  const fullText = '> asep run --mode isolated\n[INFO] Initializing sandbox...\n[SUCCESS] Environment ready.'
  
  useEffect(() => {
    let i = 0
    const interval = setInterval(() => {
      setText(fullText.slice(0, i))
      i++
      if (i > fullText.length) {
        setTimeout(() => { i = 0 }, 3000)
      }
    }, 50)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="w-full h-40 bg-[#090B0F] rounded-lg border border-[#202833] overflow-hidden flex flex-col font-mono text-xs mt-6">
      <div className="h-6 w-full border-b border-[#202833] bg-[#0D1117] flex items-center px-3 gap-1.5">
        <div className="w-2 h-2 rounded-full bg-red-500/50" />
        <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
        <div className="w-2 h-2 rounded-full bg-green-500/50" />
      </div>
      <div className="p-4 text-[#9CA6B5] whitespace-pre-wrap flex-1 flex flex-col leading-relaxed">
        <span>{text}<motion.span animate={{ opacity: [1, 0] }} transition={{ repeat: Infinity, duration: 0.8 }}>|</motion.span></span>
      </div>
    </div>
  )
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
            ease: "easeInOut",
            delay: i * 0.4
          }}
          style={{
            transform: `rotateX(60deg) rotateZ(-45deg) translateZ(${i * 20}px)`,
          }}
          className={cn(
            "absolute w-24 h-24 rounded-xl border flex items-center justify-center shadow-xl transition-all",
            i === 2 ? "bg-[#22D3EE]/10 border-[#22D3EE]/50 backdrop-blur-md" : 
            i === 1 ? "bg-[#2DD4A3]/5 border-[#2DD4A3]/30 backdrop-blur-sm" : 
            "bg-[#111720]/80 border-[#202833]"
          )}
        >
          {i === 2 && <Layers className="w-8 h-8 text-[#22D3EE] opacity-60" style={{ transform: 'rotateZ(45deg) rotateX(-60deg)' }} />}
        </motion.div>
      ))}
    </div>
  )
}

function GovernanceVisual() {
  return (
    <div className="w-full h-40 flex items-center justify-center gap-4 mt-6">
      <div className="bg-[#090B0F] border border-[#202833] rounded-lg p-4 flex flex-col gap-3 w-56 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-10 -right-10 w-20 h-20 bg-[#2DD4A3]/10 rounded-full blur-2xl" />
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[#111720] border border-[#202833] flex items-center justify-center z-10">
            <motion.div 
              animate={{ rotate: 360 }} 
              transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
            >
              <BrainCircuit className="w-4 h-4 text-[#2DD4A3]" />
            </motion.div>
          </div>
          <div className="flex flex-col gap-1.5 flex-1">
             <div className="h-2 w-full bg-[#202833] rounded-full" />
             <div className="h-2 w-2/3 bg-[#202833] rounded-full" />
          </div>
        </div>
        <div className="h-1.5 w-full bg-[#202833] rounded-full mt-1" />
        <div className="flex gap-2 mt-2 z-10">
          <motion.button 
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 bg-[#2DD4A3]/10 border border-[#2DD4A3]/30 rounded-md text-[#2DD4A3] text-[11px] font-medium py-1.5 flex justify-center items-center gap-1.5 cursor-pointer"
          >
            <Check className="w-3 h-3" /> Approve
          </motion.button>
          <motion.button 
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="flex-1 bg-red-500/10 border border-red-500/30 rounded-md text-red-400 text-[11px] font-medium py-1.5 flex justify-center items-center cursor-pointer"
          >
            Reject
          </motion.button>
        </div>
      </div>
    </div>
  )
}

function EvaluationVisual() {
  return (
    <div className="w-full h-40 flex items-center justify-center mt-6">
      <div className="relative flex items-center justify-center">
        <svg className="w-28 h-28 transform -rotate-90 drop-shadow-lg">
          <circle cx="56" cy="56" r="46" stroke="#202833" strokeWidth="8" fill="none" />
          <motion.circle 
            cx="56" cy="56" r="46" 
            stroke="#2DD4A3" 
            strokeWidth="8" 
            fill="none" 
            strokeDasharray="289"
            initial={{ strokeDashoffset: 289 }}
            whileInView={{ strokeDashoffset: 28.9 }}
            transition={{ duration: 1.5, ease: "easeOut", delay: 0.2 }}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-[#F5F7FA] font-bold text-2xl tracking-tight">90%</span>
          <span className="text-[#9CA6B5] text-[10px] uppercase font-mono tracking-wider mt-0.5">Score</span>
        </div>
      </div>
    </div>
  )
}

function ControlPlaneVisual() {
  return (
    <div className="w-full h-40 bg-[#090B0F] border border-[#202833] rounded-lg p-4 flex flex-col justify-end relative overflow-hidden mt-6">
      <div className="absolute top-0 right-0 p-4 flex gap-1.5">
        <div className="w-1.5 h-3 bg-[#22D3EE] rounded-sm animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.5)]" />
        <div className="w-1.5 h-4 bg-[#22D3EE]/70 rounded-sm animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.3)]" style={{ animationDelay: '0.2s' }} />
        <div className="w-1.5 h-2 bg-[#22D3EE]/40 rounded-sm animate-pulse" style={{ animationDelay: '0.4s' }} />
      </div>
      <div className="absolute top-4 left-4 text-[10px] font-mono text-[#9CA6B5]">ACTIVE METRICS</div>
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
  )
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
  ]

  return (
    <section className="py-24 bg-[#090B0F] relative overflow-hidden">
      {/* Background elements */}
      <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-[#202833] to-transparent" />
      <div className="absolute top-[-20%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[#22D3EE]/5 blur-[120px] pointer-events-none" />
      
      <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-10">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-100px" }}
          variants={fadeUpVariant}
          className="text-center max-w-3xl mx-auto mb-20"
        >
          <h2 className="text-3xl md:text-5xl font-bold text-[#F5F7FA] tracking-tight mb-6">
            Architected for <span className="relative whitespace-nowrap">
              Scale
              <span className="absolute -bottom-2 left-0 w-full h-1 bg-gradient-to-r from-[#22D3EE] to-[#2DD4A3] rounded-full" />
            </span>
          </h2>
          <p className="text-lg text-[#9CA6B5] leading-relaxed">
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
                "group relative bg-[#0D1117] rounded-2xl border border-[#202833] p-6 flex flex-col justify-between transition-all duration-300 overflow-hidden",
                feature.span,
                feature.accentClass
              )}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              
              <div className="relative z-10">
                <div className="flex items-center gap-4 mb-4">
                  <motion.div 
                    className="p-2.5 rounded-xl bg-[#111720] border border-[#202833] group-hover:border-transparent transition-colors"
                    whileHover={{ y: -2 }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    {feature.icon}
                  </motion.div>
                  <h3 className="text-xl font-semibold text-[#F5F7FA]">{feature.title}</h3>
                </div>
                <p className="text-[#9CA6B5] leading-relaxed text-sm">
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
  )
}
