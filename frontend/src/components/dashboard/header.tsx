"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Search, Bell, User } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { SidebarNav } from "@/components/dashboard/sidebar";
import { useAuth } from "@/lib/providers/auth-provider";

export function DashboardHeader() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [isProfileOpen, setIsProfileOpen] = React.useState(false);
  const pathname = usePathname();
  const { logout } = useAuth();

  // Simple breadcrumb generator based on pathname
  const pathSegments = pathname.split("/").filter(Boolean);
  const breadcrumb =
    pathSegments.length > 0
      ? pathSegments[0].charAt(0).toUpperCase() + pathSegments[0].slice(1)
      : "Overview";

  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center gap-x-4 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      {/* Mobile Sidebar Toggle */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden -m-2.5 p-2.5 text-muted-foreground"
          >
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-5 w-5" aria-hidden="true" />
          </Button>
        </SheetTrigger>
        <SheetContent
          side="left"
          className="p-0 w-64 border-r border-border/50"
        >
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
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground"
            aria-label="Search"
          >
            <Search className="h-4 w-4" />
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
          </Button>

          <div
            className="hidden lg:block h-6 w-px bg-border"
            aria-hidden="true"
          />

          <ThemeToggle />

          {/* Profile Menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="rounded-full bg-secondary/50"
              aria-label="User profile"
              onClick={() => setIsProfileOpen(!isProfileOpen)}
            >
              <User className="h-4 w-4 text-muted-foreground" />
            </Button>

            {isProfileOpen && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setIsProfileOpen(false)} 
                />
                <div className="absolute right-0 mt-2 w-48 rounded-md border border-border bg-popover text-popover-foreground shadow-md z-50 overflow-hidden flex flex-col py-1">
                  <div className="px-4 py-2 border-b border-border/50 text-xs font-semibold uppercase text-muted-foreground">
                    Account
                  </div>
                  <Link href="/settings?tab=profile" onClick={() => setIsProfileOpen(false)} className="px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground cursor-pointer">
                    Profile
                  </Link>
                  <Link href="/settings?tab=account" onClick={() => setIsProfileOpen(false)} className="px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground cursor-pointer">
                    Settings
                  </Link>
                  <div className="border-t border-border/50 my-1" />
                  <button
                    className="px-4 py-2 text-sm text-left hover:bg-accent hover:text-accent-foreground cursor-pointer w-full"
                    onClick={() => {
                      setIsProfileOpen(false);
                      if (window.confirm("Are you sure you want to log out?")) {
                        logout();
                      }
                    }}
                  >
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
