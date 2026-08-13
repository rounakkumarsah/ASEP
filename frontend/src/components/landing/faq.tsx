"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus, ExternalLink, ArrowRight, BookOpen, Github, MessageSquare, Mail } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { Button } from "@/components/ui/button";

const faqs = [
  {
    question: "How does ASEP differ from a standard CI/CD pipeline?",
    answer:
      "While CI/CD pipelines automate testing and deployment of code you write, ASEP provides an autonomous agent runtime that actually writes, debugs, and refactors the code for you based on high-level objectives, operating securely within your local environment.",
    category: "Platform",
  },
  {
    question: "Is my codebase data sent to external servers?",
    answer:
      "No. ASEP is designed for enterprise security. You can run the entire agent runtime locally or in your private VPC. We support local LLMs via Ollama or vLLM, ensuring zero data retention and strict compliance with SOC2/HIPAA requirements.",
    category: "Security",
  },
  {
    question: "Can I enforce human-in-the-loop (HITL) approvals?",
    answer:
      "Yes. Our Governance layer allows you to set granular policies. For example, you can require human approval before any agent commits to the main branch, modifies production databases, or executes destructive terminal commands.",
    category: "Security",
  },
  {
    question: "What languages and frameworks are supported?",
    answer:
      "ASEP is language-agnostic at its core since it operates via standard terminal, git, and file-system tools. However, it comes pre-configured with deep semantic understanding and tooling for TypeScript, Python, Rust, and Go.",
    category: "Technical",
  },
  {
    question: "How does pricing work for the Enterprise tier?",
    answer:
      "Enterprise pricing is custom-tailored based on your deployment needs (air-gapped vs VPC), the number of active orchestration nodes, and required SLA guarantees. Contact our sales team for a precise quote.",
    category: "Pricing",
  },
  {
    question: "Can I run ASEP with local LLMs like Ollama?",
    answer:
      "Yes. ASEP fully supports local LLM backends including Ollama, vLLM, and LM Studio. You configure the model endpoint in your .env file, and the entire agent runtime operates entirely within your infrastructure with zero external API calls.",
    category: "Technical",
  },
  {
    question: "What is the Model Context Protocol (MCP) integration?",
    answer:
      "The MCP Tool Registry is ASEP's dynamic tool exposure layer. It allows agents to access file system operations, terminal commands, Git operations, Slack notifications, and custom tooling through a standardized protocol, enabling flexible enterprise workflows without code changes.",
    category: "Platform",
  },
];

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="relative py-20 sm:py-28 md:py-32 bg-background dark:bg-[#090B0F] border-b border-border overflow-hidden transition-colors duration-300">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="mb-14 sm:mb-16 max-w-2xl">
          <div className="inline-flex items-center rounded-full border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] px-3 py-1 mb-5 sm:mb-6 shadow-sm">
            <span className="text-xs font-semibold tracking-wide text-primary">FREQUENTLY ASKED</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-3 sm:mb-4">
            Everything about ASEP, answered
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground leading-relaxed">
            Explore our most common questions about security, technical capabilities, and platform features.
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-10 lg:gap-8 xl:gap-14 items-start">
          {/* LEFT: FAQ Accordion (70%) */}
          <div className="lg:w-[70%] space-y-3.5 w-full">
            {faqs.map((faq, index) => {
              const isOpen = openIndex === index;
              const numStr = (index + 1).toString().padStart(2, '0');

              return (
                <motion.div
                  key={index}
                  className={cn(
                    "border rounded-2xl overflow-hidden transition-all duration-200 shadow-sm",
                    isOpen 
                      ? "bg-card dark:bg-[#111720] border-primary/50 shadow-[0_0_20px_rgba(34,211,238,0.1)]" 
                      : "bg-card/70 dark:bg-[#0D1117] border-border/80 dark:border-[#202833] hover:border-primary/30"
                  )}
                  initial={false}
                >
                  <button
                    className="flex w-full items-center text-left p-5 sm:px-7 sm:py-5 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-2xl"
                    onClick={() => setOpenIndex(isOpen ? null : index)}
                    aria-expanded={isOpen}
                    aria-controls={`faq-answer-${index}`}
                  >
                    <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-5 pr-6">
                      <span className={cn(
                        "text-xs sm:text-sm font-mono font-bold transition-colors",
                        isOpen ? "text-primary" : "text-muted-foreground"
                      )}>
                        {numStr}
                      </span>
                      <div className="flex flex-col gap-1.5">
                        <span className="text-foreground font-semibold text-base sm:text-lg leading-snug">
                          {faq.question}
                        </span>
                        <span className="inline-flex w-max items-center rounded-md border border-border/80 dark:border-[#202833] bg-muted/50 dark:bg-[#090B0F] px-2 py-0.5 text-[9px] font-mono font-medium uppercase tracking-wider text-muted-foreground">
                          {faq.category}
                        </span>
                      </div>
                    </div>
                    
                    <div
                      className={cn(
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all duration-200",
                        isOpen
                          ? "bg-primary text-[#090B0F] rotate-180 shadow-sm"
                          : "bg-muted/60 dark:bg-[#090B0F] border border-border/80 text-muted-foreground"
                      )}
                    >
                      {isOpen ? <Minus className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                    </div>
                  </button>
                  
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        id={`faq-answer-${index}`}
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: [0.04, 0.62, 0.23, 0.98] }}
                      >
                        <div className="px-5 pb-5 pt-1 sm:px-7 sm:pb-6 sm:pt-0 sm:pl-[4.5rem]">
                          <p className="text-muted-foreground text-sm sm:text-base leading-relaxed">
                            {faq.answer}
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
            
            {/* Compact CTA Row */}
            <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-border/80 dark:border-[#202833] mt-8">
              <span className="text-foreground font-medium text-sm">Still have questions?</span>
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="outline" className="border-border text-foreground hover:bg-accent rounded-xl text-xs font-mono min-h-[40px]">
                  <Mail className="w-3.5 h-3.5 mr-2" />
                  Email Support
                </Button>
                <Button variant="outline" className="border-border text-foreground hover:bg-accent rounded-xl text-xs font-mono min-h-[40px]">
                  <MessageSquare className="w-3.5 h-3.5 mr-2" />
                  Community Discord
                </Button>
              </div>
            </div>
          </div>

          {/* RIGHT: Quick Links Sidebar (30%) */}
          <div className="lg:w-[30%] w-full">
            <div className="sticky top-24 rounded-2xl border border-border/80 dark:border-[#202833] bg-card dark:bg-[#0D1117] p-5 sm:p-7 shadow-sm space-y-6">
              <h3 className="text-foreground font-semibold text-base sm:text-lg tracking-tight">Quick Links</h3>
              <ul className="space-y-2.5">
                <li>
                  <Link href="/documentation" className="group flex items-center justify-between p-3 rounded-xl hover:bg-accent transition-colors border border-transparent hover:border-border min-h-[44px]">
                    <div className="flex items-center gap-3">
                      <BookOpen className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      <span className="text-foreground text-sm font-medium">Documentation</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  </Link>
                </li>
                <li>
                  <Link href="/architecture" className="group flex items-center justify-between p-3 rounded-xl hover:bg-accent transition-colors border border-transparent hover:border-border min-h-[44px]">
                    <div className="flex items-center gap-3">
                      <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      <span className="text-foreground text-sm font-medium">Architecture</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  </Link>
                </li>
                <li>
                  <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank" rel="noreferrer" className="group flex items-center justify-between p-3 rounded-xl hover:bg-accent transition-colors border border-transparent hover:border-border min-h-[44px]">
                    <div className="flex items-center gap-3">
                      <Github className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      <span className="text-foreground text-sm font-medium">GitHub Repository</span>
                    </div>
                    <ExternalLink className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                  </Link>
                </li>
              </ul>
              
              <div className="bg-muted/40 dark:bg-[#111720] rounded-xl p-4 sm:p-5 border border-border/80 dark:border-[#202833]">
                <h4 className="text-foreground font-semibold mb-1.5 text-sm">Enterprise Needs?</h4>
                <p className="text-muted-foreground text-xs mb-3.5 leading-relaxed">
                  Discuss air-gapped deployments, custom SLA, and volume pricing.
                </p>
                <Link href="/contact" className="block w-full">
                  <Button className="w-full bg-foreground text-background hover:bg-foreground/90 font-mono font-bold text-xs rounded-xl min-h-[40px]">
                    Contact Sales
                  </Button>
                </Link>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </section>
  );
}
