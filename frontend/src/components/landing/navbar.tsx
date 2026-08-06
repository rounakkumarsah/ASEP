"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Menu, Github, Cpu } from "lucide-react";

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

const NAV_LINKS = [
  { name: "Platform", href: "/platform" },
  { name: "Architecture", href: "/architecture" },
  { name: "Documentation", href: "/documentation" },
  { name: "Pricing", href: "/pricing" },
  { name: "About", href: "/about" },
  { name: "Contact", href: "/contact" },
];

export function LandingNavbar() {
  const [isScrolled, setIsScrolled] = React.useState(false);
  const pathname = usePathname();

  React.useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-200 ${
        isScrolled
          ? "bg-[#090B0F]/90 backdrop-blur-md border-b border-[#202833] shadow-xs"
          : "bg-transparent border-b border-transparent"
      }`}
    >
      <nav className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left: Logo */}
        <div className="flex items-center">
          <Link href="/" className="flex items-center space-x-2.5 group">
            <div className="p-1 rounded bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/50 transition-colors">
              <Cpu className="h-4 w-4" />
            </div>
            <span className="font-mono font-bold tracking-wider text-sm text-[#F5F7FA]">ASEP</span>
          </Link>
        </div>

        {/* Center: Desktop Links */}
        <div className="hidden md:flex md:items-center md:space-x-1 lg:space-x-2">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className="relative px-3 py-1.5 text-xs font-mono font-medium text-[#9CA6B5] transition-colors hover:text-[#F5F7FA] group"
                aria-current={isActive ? "page" : undefined}
              >
                {link.name}
                {isActive && (
                  <motion.div
                    layoutId="navbar-active-indicator"
                    className="absolute bottom-0 left-3 right-3 h-0.5 bg-[#22D3EE]"
                    initial={false}
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        {/* Right: Actions */}
        <div className="hidden md:flex md:items-center md:space-x-2 lg:space-x-3">
          <ThemeToggle />

          <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank">
            <Button variant="ghost" size="icon" className="h-8 w-8 text-[#9CA6B5] hover:text-[#F5F7FA]" aria-label="GitHub">
              <Github className="h-4 w-4" />
            </Button>
          </Link>

          <Link href="/login">
            <Button variant="ghost" className="text-xs font-mono font-medium text-[#9CA6B5] hover:text-[#F5F7FA] h-8 px-3">
              Login
            </Button>
          </Link>

          <Link href="/signup">
            <Button className="text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-8 px-3">Get Started</Button>
          </Link>
        </div>

        {/* Mobile: Hamburger & Drawer */}
        <div className="flex items-center md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="text-[#9CA6B5] hover:text-[#F5F7FA]" aria-label="Open mobile menu">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="left"
              className="flex flex-col w-[300px] sm:w-[350px] bg-[#0D1117] border-r border-[#202833] text-[#F5F7FA]"
            >
              <SheetHeader>
                <SheetTitle className="flex items-center space-x-2">
                  <Cpu className="h-5 w-5 text-[#22D3EE]" />
                  <span className="font-mono font-bold tracking-wider text-sm text-[#F5F7FA]">ASEP</span>
                </SheetTitle>
              </SheetHeader>

              <div className="flex flex-col space-y-3 py-6 flex-1 font-mono text-sm">
                {NAV_LINKS.map((link) => (
                  <SheetClose asChild key={link.name}>
                    <Link
                      href={link.href}
                      className="text-[#9CA6B5] transition-colors hover:text-[#F5F7FA] py-1"
                    >
                      {link.name}
                    </Link>
                  </SheetClose>
                ))}
              </div>

              <div className="flex flex-col space-y-3 border-t border-[#202833] pt-4 pb-4">
                <div className="flex items-center space-x-3">
                  <ThemeToggle />

                  <Link
                    href="https://github.com/rounakkumarsah/ASEP"
                    target="_blank"
                  >
                    <Button variant="outline" size="icon" className="h-8 w-8 border-[#202833] bg-[#111720]" aria-label="GitHub">
                      <Github className="h-4 w-4 text-[#9CA6B5]" />
                    </Button>
                  </Link>
                </div>

                <div className="flex flex-col space-y-2 pt-2">
                  <SheetClose asChild>
                    <Link href="/login">
                      <Button
                        variant="outline"
                        className="w-full justify-center text-xs font-mono border-[#202833] bg-[#111720] text-[#F5F7FA]"
                      >
                        Login
                      </Button>
                    </Link>
                  </SheetClose>
                  <SheetClose asChild>
                    <Link href="/signup">
                      <Button className="w-full justify-center text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F]">
                        Get Started
                      </Button>
                    </Link>
                  </SheetClose>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </nav>
    </header>
  );
}
