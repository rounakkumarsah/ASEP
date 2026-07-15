"use client"

import * as React from "react"
import { usePathname } from "next/navigation"
import { Menu, Search, Bell, User } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { SidebarNav } from "@/components/dashboard/sidebar"

export function DashboardHeader() {
  const [isOpen, setIsOpen] = React.useState(false)
  const pathname = usePathname()

  // Simple breadcrumb generator based on pathname
  const pathSegments = pathname.split("/").filter(Boolean)
  const breadcrumb = pathSegments.length > 0 
    ? pathSegments[0].charAt(0).toUpperCase() + pathSegments[0].slice(1)
    : "Overview"

  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center gap-x-4 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      {/* Mobile Sidebar Toggle */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="lg:hidden -m-2.5 p-2.5 text-muted-foreground">
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-5 w-5" aria-hidden="true" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-64 border-r border-border/50">
          <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
          <SidebarNav onClick={() => setIsOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Separator for Mobile */}
      <div className="h-6 w-px bg-border lg:hidden" aria-hidden="true" />

      {/* Breadcrumb Area */}
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <div className="flex flex-1 items-center">
          <h1 className="text-sm font-semibold leading-6 text-foreground">
            {breadcrumb}
          </h1>
        </div>
        
        {/* Right Actions */}
        <div className="flex items-center gap-x-2 lg:gap-x-4">
          <Button variant="ghost" size="icon" className="text-muted-foreground" aria-label="Search">
            <Search className="h-4 w-4" />
          </Button>
          
          <Button variant="ghost" size="icon" className="text-muted-foreground" aria-label="Notifications">
            <Bell className="h-4 w-4" />
          </Button>
          
          <div className="hidden lg:block h-6 w-px bg-border" aria-hidden="true" />
          
          <ThemeToggle />
          
          {/* Profile Menu Placeholder */}
          <Button variant="ghost" size="icon" className="rounded-full bg-secondary/50" aria-label="User profile">
            <User className="h-4 w-4 text-muted-foreground" />
          </Button>
        </div>
      </div>
    </header>
  )
}
