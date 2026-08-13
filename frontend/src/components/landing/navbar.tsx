'use client'

import * as React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, useScroll, useSpring, useMotionValueEvent } from 'framer-motion'
import { Menu, Github, Cpu, X, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetClose
} from '@/components/ui/sheet'

const navLinks = [
  { name: 'Platform', href: '/platform' },
  { name: 'Architecture', href: '/architecture' },
  { name: 'Documentation', href: '/documentation' },
  { name: 'Pricing', href: '/pricing' },
  { name: 'About', href: '/about' },
]

export function LandingNavbar() {
  const [isScrolled, setIsScrolled] = React.useState(false)
  const pathname = usePathname()
  const { scrollYProgress, scrollY } = useScroll()

  // Scroll progress for the top indicator
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  })

  useMotionValueEvent(scrollY, 'change', (latest) => {
    setIsScrolled(latest > 50)
  })

  return (
    <>
      {/* Scroll Progress Bar */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-[#22D3EE] to-[#2DD4A3] z-[100] origin-left"
        style={{ scaleX }}
      />
      
      <header
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ease-in-out ${
          isScrolled 
            ? 'mt-4 mx-4 md:mx-auto max-w-7xl' 
            : 'w-full border-b border-[#202833]'
        }`}
      >
        <div 
          className={`flex items-center justify-between transition-all duration-300 ${
            isScrolled
              ? 'h-14 px-6 rounded-full bg-[#0D1117]/70 backdrop-blur-xl border border-[#202833] shadow-[0_0_15px_rgba(34,211,238,0.05)]'
              : 'h-16 px-6 md:px-8 bg-[#090B0F]/90 backdrop-blur-sm'
          }`}
        >
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <motion.div
              whileHover={{ scale: 1.1 }}
              transition={{ type: 'spring', stiffness: 400, damping: 10 }}
              className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-[#22D3EE] to-[#2DD4A3]/80 p-1.5"
            >
              <Cpu className="w-full h-full text-[#090B0F]" />
            </motion.div>
            <span className="font-bold text-xl tracking-tight text-[#F5F7FA]">
              ASEP
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden lg:flex items-center gap-8">
            {navLinks.map((link) => {
              const isActive = pathname === link.href
              return (
                <Link
                  key={link.name}
                  href={link.href}
                  className={`text-sm font-medium transition-colors hover:text-[#22D3EE] ${
                    isActive ? 'text-[#F5F7FA]' : 'text-[#9CA6B5]'
                  }`}
                >
                  {link.name}
                </Link>
              )
            })}
          </nav>

          {/* Right Side Actions */}
          <div className="hidden md:flex items-center gap-4">
            <div className="px-2.5 py-1 text-xs font-mono font-medium rounded-md bg-[#111720] text-[#667085] border border-[#202833]">
              v0.1.0
            </div>
            
            <Link 
              href="https://github.com/asep" 
              target="_blank"
              className="hidden lg:flex items-center gap-2 h-9 px-3 rounded-md bg-[#111720] hover:bg-[#202833] border border-[#202833] text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors text-sm font-medium"
            >
              <Github className="w-4 h-4" />
              <span>Star</span>
              <div className="h-4 w-[1px] bg-[#202833] mx-1" />
              <span className="text-[#F5F7FA]">128</span>
            </Link>
            
            <ThemeToggle />

            <div className="flex items-center gap-3 pl-4 border-l border-[#202833]">
              <Button variant="ghost" className="text-sm font-medium text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720]">
                Login
              </Button>
              <Button className="text-sm font-medium bg-[#F5F7FA] text-[#090B0F] hover:bg-[#22D3EE] hover:text-[#090B0F] transition-all shadow-[0_0_15px_rgba(34,211,238,0.2)] hover:shadow-[0_0_25px_rgba(34,211,238,0.4)]">
                Get Started
              </Button>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden text-[#F5F7FA] hover:bg-[#111720]">
                <Menu className="w-5 h-5" />
                <span className="sr-only">Toggle Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-full sm:max-w-md bg-[#0D1117] border-l border-[#202833] p-0 flex flex-col">
              <SheetHeader className="p-6 border-b border-[#202833] flex flex-row items-center justify-between space-y-0 text-left">
                <SheetTitle asChild>
                  <Link href="/" className="flex items-center gap-2 group">
                    <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-[#22D3EE] to-[#2DD4A3]/80 p-1.5">
                      <Cpu className="w-full h-full text-[#090B0F]" />
                    </div>
                    <span className="font-bold text-xl tracking-tight text-[#F5F7FA]">
                      ASEP
                    </span>
                  </Link>
                </SheetTitle>
                <SheetClose asChild>
                  <Button variant="ghost" size="icon" className="text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720]">
                    <X className="w-5 h-5" />
                  </Button>
                </SheetClose>
              </SheetHeader>
              
              <div className="flex-1 overflow-y-auto py-6 px-4">
                <nav className="flex flex-col gap-2">
                  {navLinks.map((link) => {
                    const isActive = pathname === link.href
                    return (
                      <SheetClose asChild key={link.name}>
                        <Link
                          href={link.href}
                          className={`flex items-center justify-between p-4 rounded-xl transition-colors ${
                            isActive 
                              ? 'bg-[#111720] text-[#22D3EE] border border-[#202833]' 
                              : 'text-[#F5F7FA] hover:bg-[#111720] hover:text-[#22D3EE]'
                          }`}
                        >
                          <span className="font-medium">{link.name}</span>
                          <ChevronRight className={`w-4 h-4 ${isActive ? 'text-[#22D3EE]' : 'text-[#667085]'}`} />
                        </Link>
                      </SheetClose>
                    )
                  })}
                </nav>

                <div className="mt-8 px-2 space-y-4">
                  <Button className="w-full h-11 bg-[#F5F7FA] text-[#090B0F] hover:bg-[#22D3EE] hover:text-[#090B0F] transition-all shadow-[0_0_15px_rgba(34,211,238,0.2)]">
                    Get Started
                  </Button>
                  <Button variant="outline" className="w-full h-11 border-[#202833] text-[#F5F7FA] hover:bg-[#111720]">
                    Login
                  </Button>
                </div>
              </div>

              <div className="p-6 border-t border-[#202833] bg-[#090B0F]">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-[#9CA6B5]">
                    <div className="w-2 h-2 rounded-full bg-[#2DD4A3] shadow-[0_0_8px_rgba(45,212,163,0.5)] animate-pulse"></div>
                    All systems operational
                  </div>
                  <span className="font-mono text-[#667085]">v0.1.0</span>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </header>
    </>
  )
}
