"use client";

import { cn } from "@/lib/utils";
import React, { useState } from "react";

export function BentoGrid({
  className,
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "grid md:auto-rows-[20rem] grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto",
        className
      )}
    >
      {children}
    </div>
  );
}

export function BentoGridItem({
  className,
  title,
  description,
  header,
  icon,
}: {
  className?: string;
  title?: string | React.ReactNode;
  description?: string | React.ReactNode;
  header?: React.ReactNode;
  icon?: React.ReactNode;
}) {
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setCoords({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        "relative row-span-1 rounded-2xl group/bento transition-all duration-300 p-6 border border-[#202833] bg-[#0D1117]/60 overflow-hidden flex flex-col justify-between space-y-4 cursor-default backdrop-blur-xs",
        isHovered ? "shadow-[0_8px_30px_rgb(0,0,0,0.6)] translate-y-[-2px] border-[#22D3EE]/20" : "shadow-none",
        className
      )}
    >
      {/* Spotlight glow overlay */}
      {isHovered && (
        <div
          className="absolute pointer-events-none inset-0 transition-opacity duration-300"
          style={{
            background: `radial-gradient(350px circle at ${coords.x}px ${coords.y}px, rgba(34, 211, 238, 0.08), transparent 80%)`,
          }}
        />
      )}

      {/* Interactive visual helper overlay */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-white/[0.01] to-transparent" />

      <div className="z-10 flex flex-col h-full justify-between">
        {header}
        <div className="group-hover/bento:translate-x-1.5 transition-transform duration-300">
          <div className="p-2.5 rounded-xl bg-[#22D3EE]/5 text-[#22D3EE] w-fit mb-4 border border-[#22D3EE]/10 group-hover/bento:bg-[#22D3EE]/10 group-hover/bento:border-[#22D3EE]/25 transition-all">
            {icon}
          </div>
          <div className="font-sans font-bold text-[#F5F7FA] mb-2 mt-2 text-base tracking-tight">
            {title}
          </div>
          <div className="font-sans font-normal text-[#9CA6B5] text-xs leading-relaxed">
            {description}
          </div>
        </div>
      </div>
    </div>
  );
}
