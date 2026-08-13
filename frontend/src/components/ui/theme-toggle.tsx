"use client";

import * as React from "react";
import { Moon, Sun, Laptop } from "lucide-react";
import { useTheme } from "next-themes";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
  variant?: "ghost" | "outline" | "default";
  size?: "default" | "sm" | "lg" | "icon";
}

export function ThemeToggle({
  className,
  variant = "ghost",
  size = "icon",
}: ThemeToggleProps) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button
        variant={variant}
        size={size}
        className={cn(
          "h-10 w-10 min-h-[44px] min-w-[44px] rounded-xl border border-border/40 bg-background/50 text-muted-foreground",
          className
        )}
        aria-label="Toggle theme"
      >
        <span className="h-4 w-4 block opacity-0" />
      </Button>
    );
  }

  // Cycle: dark -> light -> system -> dark
  const handleToggle = () => {
    if (theme === "dark") {
      setTheme("light");
    } else if (theme === "light") {
      setTheme("system");
    } else {
      setTheme("dark");
    }
  };

  const isDark = resolvedTheme === "dark";
  const isSystem = theme === "system";

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleToggle}
      className={cn(
        "relative h-10 w-10 min-h-[44px] min-w-[44px] rounded-xl border border-border/60 bg-background/70 hover:bg-accent hover:border-primary/40 text-foreground transition-all duration-200 overflow-hidden shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
        className
      )}
      aria-label={`Current theme: ${theme}. Click to cycle Light / Dark / System.`}
      title={`Theme: ${theme ?? "system"} (Click to cycle Light / Dark / System)`}
    >
      <AnimatePresence mode="wait" initial={false}>
        {isSystem ? (
          <motion.div
            key="system"
            initial={{ opacity: 0, scale: 0.5, rotate: -90 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            exit={{ opacity: 0, scale: 0.5, rotate: 90 }}
            transition={{ duration: 0.18 }}
            className="flex items-center justify-center"
          >
            <Laptop className="h-4 w-4 text-cyan-500" />
          </motion.div>
        ) : isDark ? (
          <motion.div
            key="dark"
            initial={{ opacity: 0, scale: 0.5, rotate: -90 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            exit={{ opacity: 0, scale: 0.5, rotate: 90 }}
            transition={{ duration: 0.18 }}
            className="flex items-center justify-center"
          >
            <Moon className="h-4 w-4 text-cyan-400" />
          </motion.div>
        ) : (
          <motion.div
            key="light"
            initial={{ opacity: 0, scale: 0.5, rotate: -90 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            exit={{ opacity: 0, scale: 0.5, rotate: 90 }}
            transition={{ duration: 0.18 }}
            className="flex items-center justify-center"
          >
            <Sun className="h-4 w-4 text-amber-500" />
          </motion.div>
        )}
      </AnimatePresence>
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
