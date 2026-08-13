"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface TimelineProps {
  className?: string;
  children: React.ReactNode;
}

export function Timeline({ className, children }: TimelineProps) {
  return (
    <div className={cn("relative ml-3 space-y-8 before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-border before:to-transparent", className)}>
      {children}
    </div>
  );
}

interface TimelineItemProps {
  className?: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

export function TimelineItem({ className, icon, children }: TimelineItemProps) {
  return (
    <div className={cn("relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active", className)}>
      {/* Icon */}
      <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-background bg-muted text-muted-foreground shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 group-hover:bg-primary group-hover:text-primary-foreground group-hover:scale-110 transition-all duration-300 z-10">
        {icon}
      </div>
      {/* Card */}
      <div className="w-[calc(100%-4rem)] md:w-[calc(50%-3rem)] p-4 rounded-xl border bg-card/50 shadow-sm transition-all duration-300 hover:shadow-md hover:border-primary/40">
        {children}
      </div>
    </div>
  );
}

export function TimelineTime({ className, children }: { className?: string, children: React.ReactNode }) {
  return <div className={cn("text-xs text-muted-foreground font-mono mb-2", className)}>{children}</div>;
}

export function TimelineTitle({ className, children }: { className?: string, children: React.ReactNode }) {
  return <h4 className={cn("font-semibold text-foreground mb-1", className)}>{children}</h4>;
}

export function TimelineContent({ className, children }: { className?: string, children: React.ReactNode }) {
  return <div className={cn("text-sm text-muted-foreground", className)}>{children}</div>;
}
