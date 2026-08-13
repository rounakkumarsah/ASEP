"use client";

import * as React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { LineShadowText } from "@/components/ui/line-shadow-text";

interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] w-full flex-col items-center justify-center rounded-xl border border-dashed border-[#202833] bg-[#090B0F]/50 p-8 text-center animate-in fade-in-50 duration-700 relative overflow-hidden group",
        className
      )}
      {...props}
    >
      {/* Background radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(34,211,238,0.03)_0%,transparent_50%)]" />

      {/* Icon with pulsing glow */}
      <div className="relative mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-[#111720] border border-[#202833] shadow-[0_0_40px_-10px_rgba(34,211,238,0.15)] group-hover:shadow-[0_0_60px_-10px_rgba(34,211,238,0.25)] transition-shadow duration-700">
        <div className="absolute inset-0 animate-ping rounded-full bg-[#22D3EE]/5 opacity-20 duration-1000" />
        <Icon className="h-10 w-10 text-[#22D3EE]" strokeWidth={1.5} />
      </div>

      <h3 className="mb-3 text-2xl tracking-tight text-[#F5F7FA]">
        <LineShadowText shadowColor="rgba(34, 211, 238, 0.2)">
          {title}
        </LineShadowText>
      </h3>

      <p className="mb-8 max-w-sm text-sm text-[#9CA6B5] font-sans leading-relaxed z-10">
        {description}
      </p>

      {action && <div className="z-10">{action}</div>}
    </div>
  );
}
