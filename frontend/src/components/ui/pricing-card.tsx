"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

interface PricingCardProps {
  name: string;
  price: string;
  period?: string;
  description: string;
  icon: LucideIcon;
  features: readonly string[];
  isPopular?: boolean;
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
  action,
}: PricingCardProps) {
  const [coords, setCoords] = React.useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = React.useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setCoords({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <motion.div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ y: -6 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      className={cn(
        "relative flex flex-col justify-between rounded-2xl p-8 transition-all duration-300 overflow-hidden backdrop-blur-md border",
        isPopular
          ? "border-[#22D3EE]/60 bg-[#0D1117]/80 shadow-[0_0_40px_-5px_rgba(34,211,238,0.2)]"
          : "border-[#202833] bg-[#111720]/40 hover:border-[#22D3EE]/30"
      )}
    >
      {/* Animated Border Beam for Popular Card */}
      {isPopular && (
        <div className="absolute inset-0 rounded-2xl pointer-events-none overflow-hidden p-[1px]">
          <div className="absolute inset-[-100%] bg-[conic-gradient(from_90deg_at_50%_50%,#090B0F_0%,#090B0F_50%,#22D3EE_75%,#090B0F_100%)] animate-[spin_6s_linear_infinite]" />
        </div>
      )}

      {/* Inner Content Container to cover the border-beam overflow background */}
      <div className="absolute inset-[1px] rounded-[15px] bg-[#0D1117] -z-10" />

      {/* Mouse Spotlight Glow */}
      {isHovered && (
        <div
          className="absolute pointer-events-none inset-0 transition-opacity duration-300"
          style={{
            background: `radial-gradient(350px circle at ${coords.x}px ${coords.y}px, rgba(34, 211, 238, 0.06), transparent 80%)`,
          }}
        />
      )}

      {isPopular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
          <span className="rounded-full bg-gradient-to-r from-[#22D3EE] to-[#67E8F9] px-3.5 py-1 text-[9px] font-mono font-bold uppercase tracking-wider text-[#090B0F] shadow-lg">
            Most Popular
          </span>
        </div>
      )}
      
      {/* Header */}
      <div className="relative z-10 mb-5 flex items-center gap-3">
        <div className={cn("p-2.5 rounded-xl border", isPopular ? "bg-[#22D3EE]/10 border-[#22D3EE]/30 text-[#22D3EE]" : "bg-[#111720] border-[#202833] text-[#9CA6B5]")}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-xl font-bold tracking-tight text-[#F5F7FA] font-sans">{name}</h3>
        </div>
      </div>

      <p className="relative z-10 text-sm text-[#9CA6B5] mb-6 min-h-[44px] leading-relaxed font-sans">{description}</p>

      {/* Pricing */}
      <div className="relative z-10 mb-6 flex items-baseline font-mono text-[#F5F7FA]">
        <span className="text-4xl font-extrabold tracking-tight">{price}</span>
        <span className="ml-1 text-sm text-[#667085]">{period}</span>
      </div>

      {/* Features */}
      <ul className="relative z-10 mb-8 flex-1 space-y-4">
        {features.map((feature, i) => (
          <li key={i} className="flex items-start text-sm font-sans text-[#F5F7FA]">
            <div className="rounded-full p-1 bg-[#22D3EE]/10 mr-3 mt-0.5 shrink-0 border border-[#22D3EE]/20">
              <CheckCircle2 className="h-3 w-3 text-[#22D3EE]" />
            </div>
            <span className="leading-relaxed text-[#D1D5DB]">{feature}</span>
          </li>
        ))}
      </ul>

      {/* Action */}
      <div className="relative z-10 mt-auto">
        {action}
      </div>
    </motion.div>
  );
}
