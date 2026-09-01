"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Search, Bell, User, LogOut, Settings as SettingsIcon } from "lucide-react";

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
  const { user, logout } = useAuth();

  // Clean breadcrumb generator
  const pathSegments = pathname.split("/").filter(Boolean);
  const breadcrumb =
    pathSegments.length > 0
      ? pathSegments[0].charAt(0).toUpperCase() + pathSegments[0].slice(1)
      : "Overview";

  return (
    <header className="sticky top-0 z-20 flex h-14 shrink-0 items-center gap-x-4 border-b border-[#202833] bg-[#0D1117] px-4 shadow-xs sm:gap-x-6 sm:px-6 lg:px-8">
      {/* Mobile Sidebar Toggle */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden -m-2.5 p-2.5 text-[#9CA6B5] hover:text-[#F5F7FA]"
          >
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-5 w-5" aria-hidden="true" />
          </Button>
        </SheetTrigger>
        <SheetContent
          side="left"
          className="p-0 w-64 border-r border-[#202833] bg-[#0D1117]"
        >
          <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
          <SidebarNav onClick={() => setIsOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Separator for Mobile */}
      <div className="h-5 w-px bg-[#202833] lg:hidden" aria-hidden="true" />

      {/* Breadcrumb Area */}
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <div className="flex flex-1 items-center space-x-2 text-xs font-mono">
          <Link href="/" className="text-[#667085] hover:text-[#F5F7FA] transition-colors">ASEP</Link>
          <span className="text-[#667085]">/</span>
          <span className="text-[#F5F7FA] font-semibold tracking-wide">{breadcrumb}</span>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-x-2 lg:gap-x-3">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720]"
            aria-label="Search"
          >
            <Search className="h-4 w-4" />
          </Button>

          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720] relative"
              aria-label="Notifications"
              onClick={() => {}} // We could toggle state, but for now we'll do a simple hover/focus group or state
            >
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-[#2DD4A3]" />
            </Button>
          </div>

          <div
            className="hidden lg:block h-5 w-px bg-[#202833]"
            aria-hidden="true"
          />

          <ThemeToggle />

          {/* Profile Dropdown Menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-md bg-[#111720] border border-[#202833] text-[#9CA6B5] hover:text-[#F5F7FA]"
              aria-label="User profile"
              onClick={() => setIsProfileOpen(!isProfileOpen)}
            >
              <User className="h-4 w-4" />
            </Button>

            {isProfileOpen && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setIsProfileOpen(false)} 
                />
                <div className="absolute right-0 mt-2 w-56 rounded-lg border border-[#202833] bg-[#0D1117] text-[#F5F7FA] shadow-xl z-50 overflow-hidden flex flex-col py-1.5 font-mono text-xs">
                  <div className="px-3 py-2 border-b border-[#202833] space-y-0.5">
                    <p className="font-semibold text-[#F5F7FA] truncate">{user?.first_name ? `${user.first_name} ${user.last_name || ""}` : user?.username}</p>
                    <p className="text-[10px] text-[#9CA6B5] truncate">{user?.email}</p>
                  </div>

                  <Link 
                    href="/settings?tab=profile" 
                    onClick={() => setIsProfileOpen(false)} 
                    className="flex items-center space-x-2 px-3 py-2 text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720] transition-colors cursor-pointer"
                  >
                    <User className="h-3.5 w-3.5 text-[#22D3EE]" />
                    <span>Profile Details</span>
                  </Link>

                  <Link 
                    href="/settings?tab=account" 
                    onClick={() => setIsProfileOpen(false)} 
                    className="flex items-center space-x-2 px-3 py-2 text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720] transition-colors cursor-pointer"
                  >
                    <SettingsIcon className="h-3.5 w-3.5 text-[#22D3EE]" />
                    <span>Account Settings</span>
                  </Link>

                  <div className="border-t border-[#202833] my-1" />

                  <button
                    className="flex items-center space-x-2 px-3 py-2 text-left text-[#F05252] hover:bg-[#111720] transition-colors cursor-pointer w-full"
                    onClick={() => {
                      setIsProfileOpen(false);
                      if (window.confirm("Are you sure you want to log out?")) {
                        logout();
                      }
                    }}
                  >
                    <LogOut className="h-3.5 w-3.5" />
                    <span>Logout</span>
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
