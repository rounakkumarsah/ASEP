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
  }
];

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="relative py-24 bg-[#090B0F] overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="mb-16 max-w-2xl">
          <div className="inline-flex items-center rounded-full border border-[#202833] bg-[#0D1117] px-3 py-1 mb-6">
            <span className="text-xs font-semibold tracking-wide text-[#22D3EE]">FREQUENTLY ASKED</span>
          </div>
          <h2 className="text-4xl font-bold tracking-tight text-[#F5F7FA] sm:text-5xl mb-4">
            Everything about ASEP, answered
          </h2>
          <p className="text-lg text-[#9CA6B5]">
            Explore our most common questions about security, technical capabilities, and platform features.
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-12 lg:gap-8 xl:gap-16">
          {/* LEFT: FAQ Accordion (70%) */}
          <div className="lg:w-[70%] space-y-4">
            {faqs.map((faq, index) => {
              const isOpen = openIndex === index;
              const numStr = (index + 1).toString().padStart(2, '0');

              return (
                <motion.div
                  key={index}
                  className={cn(
                    "border rounded-2xl overflow-hidden transition-all duration-300",
                    isOpen 
                      ? "bg-[#111720] border-[#22D3EE] shadow-[0_0_15px_rgba(34,211,238,0.1)]" 
                      : "bg-[#0D1117] border-[#202833] hover:border-[#202833]/80 hover:bg-[#111720]/50"
                  )}
                  initial={false}
                >
                  <button
                    className="flex w-full items-center text-left p-6 sm:px-8 sm:py-6 focus:outline-none"
                    onClick={() => setOpenIndex(isOpen ? null : index)}
                  >
                    <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6 pr-8">
                      <span className={cn(
                        "text-sm font-mono transition-colors",
                        isOpen ? "text-[#22D3EE]" : "text-[#667085]"
                      )}>
                        {numStr}
                      </span>
                      <div className="flex flex-col gap-2">
                        <span className="text-[#F5F7FA] font-medium text-lg leading-tight">
                          {faq.question}
                        </span>
                        <span className="inline-flex w-max items-center rounded-full border border-[#202833] bg-[#090B0F] px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-[#9CA6B5]">
                          {faq.category}
                        </span>
                      </div>
                    </div>
                    
                    <div
                      className={cn(
                        "flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all duration-300",
                        isOpen
                          ? "bg-[#22D3EE] text-[#090B0F] rotate-180"
                          : "bg-[#090B0F] border border-[#202833] text-[#9CA6B5] group-hover:text-[#F5F7FA]"
                      )}
                    >
                      {isOpen ? <Minus className="h-5 w-5" /> : <Plus className="h-5 w-5" />}
                    </div>
                  </button>
                  
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                      >
                        <div className="px-6 pb-6 pt-2 sm:px-8 sm:pb-8 sm:pt-0 sm:pl-[5.5rem]">
                          <p className="text-[#9CA6B5] text-base leading-relaxed">
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
            <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-6 border-t border-[#202833] mt-8">
              <span className="text-[#F5F7FA] font-medium">Still have questions?</span>
              <div className="flex flex-wrap items-center gap-4">
                <Button variant="outline" className="bg-transparent border-[#202833] text-[#F5F7FA] hover:bg-[#111720] hover:text-[#F5F7FA]">
                  <Mail className="w-4 h-4 mr-2" />
                  Email Support
                </Button>
                <Button variant="outline" className="bg-transparent border-[#202833] text-[#F5F7FA] hover:bg-[#111720] hover:text-[#F5F7FA]">
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Community Discord
                </Button>
              </div>
            </div>
          </div>

          {/* RIGHT: Quick Links Sidebar (30%) */}
          <div className="lg:w-[30%]">
            <div className="sticky top-24 rounded-2xl border border-[#202833] bg-[#0D1117] p-6 lg:p-8">
              <h3 className="text-[#F5F7FA] font-semibold text-lg mb-6">Quick Links</h3>
              <ul className="space-y-4 mb-8">
                <li>
                  <Link href="/documentation" className="group flex items-center justify-between p-3 rounded-lg hover:bg-[#111720] transition-colors border border-transparent hover:border-[#202833]">
                    <div className="flex items-center gap-3">
                      <BookOpen className="w-5 h-5 text-[#9CA6B5] group-hover:text-[#22D3EE] transition-colors" />
                      <span className="text-[#F5F7FA] text-sm font-medium">Documentation</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-[#667085] group-hover:text-[#F5F7FA] transition-colors" />
                  </Link>
                </li>
                <li>
                  <Link href="/architecture" className="group flex items-center justify-between p-3 rounded-lg hover:bg-[#111720] transition-colors border border-transparent hover:border-[#202833]">
                    <div className="flex items-center gap-3">
                      <ExternalLink className="w-5 h-5 text-[#9CA6B5] group-hover:text-[#22D3EE] transition-colors" />
                      <span className="text-[#F5F7FA] text-sm font-medium">Architecture</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-[#667085] group-hover:text-[#F5F7FA] transition-colors" />
                  </Link>
                </li>
                <li>
                  <Link href="https://github.com" target="_blank" rel="noreferrer" className="group flex items-center justify-between p-3 rounded-lg hover:bg-[#111720] transition-colors border border-transparent hover:border-[#202833]">
                    <div className="flex items-center gap-3">
                      <Github className="w-5 h-5 text-[#9CA6B5] group-hover:text-[#22D3EE] transition-colors" />
                      <span className="text-[#F5F7FA] text-sm font-medium">GitHub Repository</span>
                    </div>
                    <ExternalLink className="w-4 h-4 text-[#667085] group-hover:text-[#F5F7FA] transition-colors" />
                  </Link>
                </li>
              </ul>
              
              <div className="bg-[#111720] rounded-xl p-5 border border-[#202833]">
                <h4 className="text-[#F5F7FA] font-medium mb-2 text-sm">Enterprise Needs?</h4>
                <p className="text-[#9CA6B5] text-xs mb-4 leading-relaxed">
                  Discuss air-gapped deployments, custom SLA, and volume pricing.
                </p>
                <Button className="w-full bg-[#F5F7FA] text-[#090B0F] hover:bg-[#E2E8F0]">
                  Contact Sales
                </Button>
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </section>
  );
}
