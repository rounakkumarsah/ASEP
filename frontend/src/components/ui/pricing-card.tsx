"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Check, LucideIcon } from "lucide-react";
import { motion, useMotionTemplate, useMotionValue } from "framer-motion";

interface PricingCardProps {
  name: string;
  price: string;
  period?: string;
  description: string;
  icon: LucideIcon;
  features: readonly string[];
  isPopular?: boolean;
  isEnterprise?: boolean;
  action?: React.ReactNode;
}

export function PricingCard({
  name,
  price,
  period = "/month",
  description,
  icon: Icon,
  features,
  isPopular,
  isEnterprise,
  action,
}: PricingCardProps) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent<HTMLDivElement>) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  return (
    <div
      onMouseMove={handleMouseMove}
      className={cn(
        "group relative flex flex-col justify-between rounded-3xl p-8 transition-all duration-300",
        "bg-[#0D1117]/80 backdrop-blur-xl border border-white/[0.08]",
        isPopular && "shadow-[0_0_40px_-15px_rgba(34,211,238,0.2)]",
        isEnterprise && "bg-[#090B0F]/90"
      )}
    >
      {/* 21st.dev style subtle hover glow */}
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition duration-300 group-hover:opacity-100"
        style={{
          background: useMotionTemplate\
            radial-gradient(
              400px circle at \px \px,
              rgba(34, 211, 238, 0.1),
              transparent 80%
            )
          \,
        }}
      />
      
      {/* Static top glow for popular */}
      {isPopular && (
        <div className="absolute top-0 inset-x-0 h-[1px] bg-gradient-to-r from-transparent via-[#22D3EE] to-transparent opacity-50" />
      )}

      {isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <span className="rounded-full bg-[#111720] border border-[#22D3EE]/30 px-3 py-1 text-[10px] font-mono font-bold uppercase tracking-widest text-[#22D3EE] shadow-lg">
            Most Popular
          </span>
        </div>
      )}
      
      {/* Header */}
      <div className="relative z-10 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div className={cn(
            "p-2.5 rounded-xl border shadow-sm", 
            isPopular 
              ? "bg-[#22D3EE]/10 border-[#22D3EE]/30 text-[#22D3EE] shadow-[#22D3EE]/10" 
              : "bg-[#111720] border-[#202833] text-[#9CA6B5]"
          )}>
            <Icon className="h-5 w-5" />
          </div>
          <h3 className="text-xl font-semibold tracking-tight text-[#F5F7FA]">{name}</h3>
        </div>
        <p className="text-sm text-[#9CA6B5] min-h-[44px] leading-relaxed">{description}</p>
      </div>

      {/* Pricing */}
      <div className="relative z-10 mb-8 pb-8 border-b border-white/[0.08]">
        <div className="flex items-baseline font-mono">
          <span className="text-4xl font-bold tracking-tight text-[#F5F7FA]">{price}</span>
          <span className="ml-1 text-sm font-medium text-[#667085]">{period}</span>
        </div>
      </div>

      {/* Features */}
      <ul className="relative z-10 mb-8 flex-1 space-y-4">
        {features.map((feature, i) => (
          <li key={i} className="flex items-start text-sm text-[#D1D5DB]">
            <div className={cn(
              "rounded-full p-1 mr-3 mt-0.5 shrink-0 border",
              isPopular 
                ? "bg-[#22D3EE]/10 border-[#22D3EE]/20 text-[#22D3EE]" 
                : "bg-white/5 border-white/10 text-[#9CA6B5]"
            )}>
              <Check className="h-3 w-3 stroke-[3]" />
            </div>
            <span className="leading-relaxed">{feature}</span>
          </li>
        ))}
      </ul>

      {/* Action */}
      <div className="relative z-10 mt-auto">
        {action}
      </div>
    </div>
  );
}
