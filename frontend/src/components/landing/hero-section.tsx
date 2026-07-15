"use client"

import { motion, Variants } from "framer-motion"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Github } from "lucide-react"

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
  }

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } },
  }

  return (
    <section className="relative overflow-hidden bg-background pt-24 pb-32 md:pt-32 md:pb-40">
      {/* Subtle Background Elements */}
      <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/10 via-background to-background" />

      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Badge */}
          <motion.div variants={itemVariants} className="mb-8 flex justify-center">
            <span className="inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-sm font-medium text-primary shadow-sm backdrop-blur-sm">
              <span className="mr-2 flex h-2 w-2 rounded-full bg-primary" />
              v2.4 Released — Production Ready
            </span>
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={itemVariants}
            className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl md:text-6xl lg:text-7xl"
          >
            Autonomous Software Engineering at Enterprise Scale
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            variants={itemVariants}
            className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-muted-foreground sm:text-xl"
          >
            Unify Planning, Execution, Memory, and Governance. ASEP is the open-source control plane for production-grade AI agents, built for absolute reliability and scale.
          </motion.p>

          {/* CTAs */}
          <motion.div
            variants={itemVariants}
            className="mt-10 flex flex-col items-center justify-center space-y-4 sm:flex-row sm:space-x-4 sm:space-y-0"
          >
            <Link href="/login">
              <Button size="lg" className="h-12 px-8 text-base group">
                Deploy Control Plane
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank">
              <Button size="lg" variant="outline" className="h-12 px-8 text-base">
                <Github className="mr-2 h-4 w-4" />
                View Source
              </Button>
            </Link>
          </motion.div>
        </motion.div>

        {/* Dashboard Preview Mockup */}
        <motion.div
          initial={{ opacity: 0, y: 40, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.6, ease: "easeOut" }}
          className="mx-auto mt-20 max-w-5xl"
        >
          <div className="relative rounded-xl border border-white/10 bg-black/40 p-2 shadow-2xl shadow-primary/20 backdrop-blur-md sm:p-4">
            <div className="flex h-[400px] sm:h-[500px] w-full flex-col overflow-hidden rounded-lg border bg-card text-card-foreground shadow-sm md:flex-row">
              {/* Mock Sidebar */}
              <div className="hidden w-48 border-r bg-muted/20 p-4 md:block">
                <div className="mb-6 h-6 w-24 rounded bg-primary/20" />
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-8 w-full rounded bg-muted/50" />
                  ))}
                </div>
              </div>
              {/* Mock Main Area */}
              <div className="flex-1 p-6">
                <div className="mb-6 h-8 w-48 rounded bg-muted" />
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-24 rounded-lg border bg-card p-4">
                      <div className="mb-2 h-4 w-16 rounded bg-muted" />
                      <div className="h-8 w-12 rounded bg-primary/20" />
                    </div>
                  ))}
                </div>
                <div className="mt-4 h-48 w-full rounded-lg border bg-card p-4">
                  <div className="flex items-center justify-center h-full border border-dashed border-muted-foreground/30 text-muted-foreground rounded text-sm">
                    Live Session Feed
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
