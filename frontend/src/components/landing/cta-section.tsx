"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CtaSection() {
  return (
    <section className="relative py-32 overflow-hidden bg-background">
      {/* Background Spotlight Glow */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-gradient-to-t from-primary/15 to-transparent blur-3xl opacity-50 transition-opacity duration-1000" />
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="mx-auto max-w-3xl text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="text-4xl font-extrabold tracking-tight text-foreground sm:text-5xl"
          >
            Build Enterprise AI Systems,
            <br className="hidden sm:block" /> Not Just AI Workflows.
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1, ease: "easeOut" }}
            className="mt-6 text-xl leading-relaxed text-muted-foreground"
          >
            Deploy autonomous AI agents with planning, execution, memory,
            governance, evaluation, and production-ready architecture — all in
            one platform.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2, ease: "easeOut" }}
            className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link href="/signup" className="w-full sm:w-auto">
              <Button
                size="lg"
                className="w-full sm:w-auto text-base font-semibold group h-12 px-8"
              >
                Start Building
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>

            <Link href="/docs" className="w-full sm:w-auto">
              <Button
                size="lg"
                variant="outline"
                className="w-full sm:w-auto text-base font-medium h-12 px-8 border-border/60 hover:bg-muted/50"
              >
                <BookOpen className="mr-2 h-4 w-4 text-muted-foreground" />
                View Documentation
              </Button>
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
