"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

export function CtaSection() {
  return (
    <section className="relative py-28 overflow-hidden bg-[#090B0F] border-b border-[#202833]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="mx-auto max-w-3xl text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl font-extrabold tracking-tight text-[#F5F7FA] sm:text-4xl font-sans"
          >
            Build Enterprise Engineering Systems,
            <br className="hidden sm:block" /> Not Just AI Chatbots.
          </motion.h2>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-4 text-base leading-relaxed text-[#9CA6B5] font-sans"
          >
            Deploy autonomous agents with planning, execution, memory, governance, evaluation, and production-ready architecture.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link href="/signup" className="w-full sm:w-auto">
              <Button
                size="lg"
                className="w-full sm:w-auto text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] group h-11 px-6"
              >
                <span>Start Building</span>
                <ArrowRight className="ml-2 h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>

            <Link href="/documentation" className="w-full sm:w-auto">
              <Button
                size="lg"
                variant="outline"
                className="w-full sm:w-auto text-xs font-mono font-medium h-11 px-6 border-[#202833] bg-[#0D1117] text-[#F5F7FA] hover:bg-[#111720]"
              >
                <BookOpen className="mr-2 h-3.5 w-3.5 text-[#9CA6B5]" />
                <span>View Documentation</span>
              </Button>
            </Link>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
