"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-border/50 bg-card/40 p-6 transition-all duration-300 hover:shadow-[0_0_2rem_-0.5rem_#ffffff30] hover:border-primary/50",
        className
      )}
    >
      {/* Animated gradient background on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
      
      <div className="relative z-10 flex flex-row items-center justify-between pb-4">
        <h3 className="text-sm font-semibold tracking-wider text-muted-foreground uppercase">
          {title}
        </h3>
        {icon && (
          <div className="text-primary/70 transition-transform duration-300 group-hover:scale-110 group-hover:text-primary">
            {icon}
          </div>
        )}
      </div>
      
      <div className="relative z-10">
        <div className="text-3xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-br from-foreground to-foreground/70 group-hover:from-foreground group-hover:to-primary/80 transition-all duration-300">
          {value}
        </div>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-2 font-medium">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
