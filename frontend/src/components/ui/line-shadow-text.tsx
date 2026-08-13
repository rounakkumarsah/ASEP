"use client";

import { motion, MotionProps } from "framer-motion";
import { cn } from "@/lib/utils";
import React from "react";

interface LineShadowTextProps extends Omit<React.HTMLAttributes<HTMLSpanElement>, "children" | "onAnimationStart" | "onDragStart" | "onDragEnd" | "onDrag" | "ref" | "style">, MotionProps {
  className?: string;
  shadowColor?: string;
  children: React.ReactNode;
}

export function LineShadowText({
  className,
  shadowColor = "rgba(34, 211, 238, 0.3)", // Cyber cyan shadow default
  children,
  ...props
}: LineShadowTextProps) {
  return (
    <motion.span
      className={cn(
        "relative inline-flex text-transparent bg-clip-text font-bold",
        className
      )}
      style={{
        backgroundImage: "linear-gradient(to bottom right, #F5F7FA, #9CA6B5)",
        textShadow: `1px 1px 0px ${shadowColor}, 2px 2px 0px ${shadowColor}, 3px 3px 0px ${shadowColor}`,
      }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      {...props}
    >
      {children}
    </motion.span>
  );
}
