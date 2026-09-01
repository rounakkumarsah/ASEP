"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, useScroll, useSpring, useMotionValueEvent } from "framer-motion";
import { Menu, Github, Cpu, X, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose,
} from "@/components/ui/sheet";
import { useAuth } from "@/lib/providers/auth-provider";

const NAV_LINKS = [
  { name: "Platform", href: "/platform" },
  { name: "Architecture", href: "/architecture" },
  { name: "Documentation", href: "/documentation" },
  { name: "Pricing", href: "/pricing" },
  { name: "About", href: "/about" },
];

export function LandingNavbar() {
  const [isScrolled, setIsScrolled] = React.useState(false);
  const [hoveredIndex, setHoveredIndex] = React.useState<number | null>(null);
  const pathname = usePathname();
  const { scrollYProgress, scrollY } = useScroll();
  const { isAuthenticated } = useAuth();

  // Smooth scroll progress bar at top of viewport
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 30,
    restDelta: 0.001,
  });

  useMotionValueEvent(scrollY, "change", (latest) => {
    setIsScrolled(latest > 30);
  });

  return (
    <>
      {/* Scroll Progress Bar */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#22D3EE] via-[#67E8F9] to-[#2DD4A3] z-[100] origin-left"
        style={{ scaleX }}
      />

      <header
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ease-out ${
          isScrolled
            ? "mt-2 sm:mt-3 mx-2 sm:mx-4 md:mx-auto max-w-6xl"
            : "w-full border-b border-border/40"
        }`}
      >
        <div
          className={`flex items-center justify-between transition-all duration-300 ${
            isScrolled
              ? "h-14 px-3.5 sm:px-6 rounded-2xl bg-background/85 dark:bg-[#0D1117]/85 backdrop-blur-xl border border-border/80 shadow-[0_8px_32px_rgba(0,0,0,0.12)] dark:shadow-[0_8px_32px_rgba(0,0,0,0.5)]"
              : "h-16 px-4 sm:px-6 lg:px-8 bg-background/75 dark:bg-[#090B0F]/75 backdrop-blur-md"
          }`}
        >
          {/* Left: Logo & Version */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-lg min-h-[44px]"
            >
              <motion.div
                whileHover={{ scale: 1.08, rotate: 5 }}
                whileTap={{ scale: 0.95 }}
                transition={{ type: "spring", stiffness: 400, damping: 15 }}
                className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-[#22D3EE] to-[#2DD4A3] p-1.5 shadow-[0_0_12px_rgba(34,211,238,0.3)]"
              >
                <Cpu className="w-full h-full text-[#090B0F]" />
              </motion.div>
              <span className="font-bold text-lg tracking-tight text-foreground font-sans">
                ASEP
              </span>
            </Link>

            <span className="hidden sm:inline-flex items-center px-2 py-0.5 text-[10px] font-mono font-medium rounded-md bg-muted/60 text-muted-foreground border border-border/60">
              v0.1.0
            </span>
          </div>

          {/* Center: Desktop Navigation Links (Visible on lg+) */}
          <nav
            className="hidden lg:flex items-center gap-1 relative"
            onMouseLeave={() => setHoveredIndex(null)}
          >
            {NAV_LINKS.map((link, idx) => {
              const isActive = pathname === link.href;
              const isHovered = hoveredIndex === idx;

              return (
                <Link
                  key={link.name}
                  href={link.href}
                  onMouseEnter={() => setHoveredIndex(idx)}
                  className={`relative px-3.5 py-2 text-sm font-medium transition-colors rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-primary min-h-[40px] flex items-center ${
                    isActive
                      ? "text-foreground font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {isHovered && (
                    <motion.span
                      layoutId="navbar-hover"
                      className="absolute inset-0 rounded-lg bg-accent/80 dark:bg-white/[0.06] -z-10"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.3 }}
                    />
                  )}
                  {isActive && (
                    <span className="absolute bottom-0 left-3.5 right-3.5 h-[2px] bg-[#22D3EE] rounded-full shadow-[0_0_8px_#22D3EE]" />
                  )}
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Desktop Right Side: GitHub -> Login -> Get Started -> Theme Toggle */}
          <div className="hidden lg:flex items-center gap-2.5">
            {/* GitHub Star */}
            <Link
              href="https://github.com/rounakkumarsah/ASEP"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 h-10 px-3 rounded-xl bg-muted/40 hover:bg-muted border border-border/60 text-muted-foreground hover:text-foreground transition-all text-xs font-mono font-medium min-h-[44px]"
            >
              <Github className="w-3.5 h-3.5" />
              <span>Star</span>
              <div className="h-3 w-[1px] bg-border mx-0.5" />
              <span className="text-foreground font-bold">128</span>
            </Link>

            {isAuthenticated ? (
              <>
                <Link href="/login">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs font-mono font-medium text-muted-foreground hover:text-foreground hover:bg-accent/60 h-10 px-3.5 rounded-xl min-h-[44px]"
                  >
                    Login
                  </Button>
                </Link>
                <Link href="/overview">
                  <Button
                    size="sm"
                    className="h-10 px-4 text-xs font-mono font-bold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] shadow-[0_0_18px_rgba(34,211,238,0.25)] hover:shadow-[0_0_28px_rgba(34,211,238,0.45)] transition-all duration-200 rounded-xl min-h-[44px]"
                  >
                    Go to Dashboard
                  </Button>
                </Link>
              </>
            ) : (
              <>
                <Link href="/login">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs font-mono font-medium text-muted-foreground hover:text-foreground hover:bg-accent/60 h-10 px-3.5 rounded-xl min-h-[44px]"
                  >
                    Login
                  </Button>
                </Link>

                <Link href="/signup">
                  <Button
                    size="sm"
                    className="h-10 px-4 text-xs font-mono font-bold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] shadow-[0_0_18px_rgba(34,211,238,0.25)] hover:shadow-[0_0_28px_rgba(34,211,238,0.45)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 rounded-xl min-h-[44px]"
                  >
                    Get Started
                  </Button>
                </Link>
              </>
            )}

            {/* Theme Toggle */}
            <ThemeToggle />
          </div>

          {/* Mobile & Tablet Right Side: Theme Toggle -> Hamburger Menu */}
          <div className="flex lg:hidden items-center gap-2">
            {/* Theme Toggle always accessible on mobile/tablet */}
            <ThemeToggle />

            {/* Mobile Drawer Trigger */}
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-10 w-10 min-h-[44px] min-w-[44px] rounded-xl text-foreground hover:bg-accent focus-visible:ring-2 focus-visible:ring-primary border border-border/40"
                  aria-label="Open Navigation Menu"
                >
                  <Menu className="w-5 h-5" />
                </Button>
              </SheetTrigger>
              <SheetContent
                side="right"
                className="w-full sm:max-w-sm bg-background border-l border-border p-0 flex flex-col z-[110]"
              >
                <SheetHeader className="p-5 border-b border-border flex flex-row items-center justify-between space-y-0 text-left">
                  <SheetTitle asChild>
                    <Link href="/" className="flex items-center gap-2.5">
                      <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-[#22D3EE] to-[#2DD4A3] p-1.5 shadow-[0_0_10px_rgba(34,211,238,0.3)]">
                        <Cpu className="w-full h-full text-[#090B0F]" />
                      </div>
                      <span className="font-bold text-lg tracking-tight text-foreground">
                        ASEP
                      </span>
                    </Link>
                  </SheetTitle>
                  <SheetClose asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-9 w-9 min-h-[44px] min-w-[44px] rounded-xl text-muted-foreground hover:text-foreground"
                    >
                      <X className="w-4 h-4" />
                      <span className="sr-only">Close menu</span>
                    </Button>
                  </SheetClose>
                </SheetHeader>

                <div className="flex-1 overflow-y-auto py-6 px-4">
                  <nav className="flex flex-col gap-1.5">
                    {NAV_LINKS.map((link) => {
                      const isActive = pathname === link.href;
                      return (
                        <SheetClose asChild key={link.name}>
                          <Link
                            href={link.href}
                            className={`flex items-center justify-between p-3.5 rounded-xl transition-colors min-h-[44px] ${
                              isActive
                                ? "bg-accent text-primary font-semibold border border-border"
                                : "text-foreground hover:bg-accent hover:text-primary"
                            }`}
                          >
                            <span className="text-sm font-medium">{link.name}</span>
                            <ChevronRight className={`w-4 h-4 ${isActive ? "text-primary" : "text-muted-foreground"}`} />
                          </Link>
                        </SheetClose>
                      );
                    })}
                  </nav>

                  <div className="mt-8 pt-6 border-t border-border space-y-3">
                    {isAuthenticated ? (
                      <>
                        <SheetClose asChild>
                          <Link href="/login" className="block w-full">
                            <Button
                              variant="outline"
                              className="w-full h-11 min-h-[44px] border-border text-foreground hover:bg-accent font-mono text-xs rounded-xl"
                            >
                              Login
                            </Button>
                          </Link>
                        </SheetClose>
                        <SheetClose asChild>
                          <Link href="/overview" className="block w-full">
                            <Button className="w-full h-11 min-h-[44px] bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] font-mono font-bold text-xs shadow-[0_0_20px_rgba(34,211,238,0.3)] rounded-xl">
                              Go to Dashboard
                            </Button>
                          </Link>
                        </SheetClose>
                      </>
                    ) : (
                      <>
                        <SheetClose asChild>
                          <Link href="/signup" className="block w-full">
                            <Button className="w-full h-11 min-h-[44px] bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] font-mono font-bold text-xs shadow-[0_0_20px_rgba(34,211,238,0.3)] rounded-xl">
                              Get Started Free
                            </Button>
                          </Link>
                        </SheetClose>
                        <SheetClose asChild>
                          <Link href="/login" className="block w-full">
                            <Button
                              variant="outline"
                              className="w-full h-11 min-h-[44px] border-border text-foreground hover:bg-accent font-mono text-xs rounded-xl"
                            >
                              Sign In
                            </Button>
                          </Link>
                        </SheetClose>
                      </>
                    )}
                  </div>
                </div>

                <div className="p-5 border-t border-border bg-muted/30">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <span className="w-2 h-2 rounded-full bg-[#2DD4A3] shadow-[0_0_8px_rgba(45,212,163,0.5)] animate-pulse" />
                      All systems nominal
                    </div>
                    <span className="font-mono text-muted-foreground">v0.1.0</span>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>
    </>
  );
}
