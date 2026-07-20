"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Menu, Github, Hexagon } from "lucide-react";

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
  { name: "Home", href: "/" },
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
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? "bg-background/80 backdrop-blur-md border-b border-border/50 shadow-sm"
          : "bg-transparent border-transparent"
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left: Logo */}
        <div className="flex items-center">
          <Link href="/" className="flex items-center space-x-2 group">
            <Hexagon className="h-6 w-6 text-primary transition-transform group-hover:scale-110" />
            <span className="font-bold tracking-tight text-lg">ASEP</span>
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
                className="relative px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground group"
                aria-current={isActive ? "page" : undefined}
              >
                {link.name}
                {isActive && (
                  <motion.div
                    layoutId="navbar-active-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary"
                    initial={false}
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        {/* Right: Actions */}
        <div className="hidden md:flex md:items-center md:space-x-2 lg:space-x-4">
          <ThemeToggle />

          <Link href="https://github.com/rounakkumarsah/ASEP" target="_blank">
            <Button variant="ghost" size="icon" aria-label="GitHub">
              <Github className="h-5 w-5" />
            </Button>
          </Link>

          <Link href="/login">
            <Button variant="ghost" className="text-sm font-medium">
              Login
            </Button>
          </Link>

          <Link href="/signup">
            <Button className="text-sm font-medium">Get Started</Button>
          </Link>
        </div>

        {/* Mobile: Hamburger & Drawer */}
        <div className="flex items-center md:hidden">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open mobile menu">
                <Menu className="h-6 w-6" />
              </Button>
            </SheetTrigger>
            <SheetContent
              side="left"
              className="flex flex-col w-[300px] sm:w-[350px]"
            >
              <SheetHeader>
                <SheetTitle className="flex items-center space-x-2">
                  <Hexagon className="h-6 w-6 text-primary" />
                  <span className="font-bold tracking-tight">ASEP</span>
                </SheetTitle>
              </SheetHeader>

              <div className="flex flex-col space-y-4 py-8 flex-1">
                {NAV_LINKS.map((link) => (
                  <SheetClose asChild key={link.name}>
                    <Link
                      href={link.href}
                      className="text-lg font-medium text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {link.name}
                    </Link>
                  </SheetClose>
                ))}
              </div>

              <div className="flex flex-col space-y-4 border-t border-border pt-6 pb-4">
                <div className="flex items-center space-x-4">
                  <ThemeToggle />

                  <Link
                    href="https://github.com/rounakkumarsah/ASEP"
                    target="_blank"
                  >
                    <Button variant="outline" size="icon" aria-label="GitHub">
                      <Github className="h-5 w-5" />
                    </Button>
                  </Link>
                </div>

                <div className="flex flex-col space-y-2 pt-2">
                  <SheetClose asChild>
                    <Link href="/login">
                      <Button
                        variant="outline"
                        className="w-full justify-center"
                      >
                        Login
                      </Button>
                    </Link>
                  </SheetClose>
                  <SheetClose asChild>
                    <Link href="/signup">
                      <Button className="w-full justify-center">
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
