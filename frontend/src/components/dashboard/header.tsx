"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Menu, Search, Bell, User, LogOut, Settings as SettingsIcon, PanelLeft, PanelLeftClose, ChevronLeft, ChevronRight } from "lucide-react";
import { useSidebarStore } from "@/lib/stores/sidebarStore";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";

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

/** Map of known URL paths to display names */
const PATH_LABELS: Record<string, string> = {
  overview: "Overview",
  projects: "Projects",
  playground: "Playground",
  copilot: "Copilot",
  sessions: "Sessions",
  memory: "Memory",
  knowledge: "Knowledge",
  skills: "Skills",
  governance: "Governance",
  approvals: "Approvals",
  evaluation: "Evaluation",
  metrics: "Metrics",
  audit: "Audit Logs",
  settings: "Settings",
  documentation: "Documentation",
  billing: "Billing",
  "api-keys": "API Keys",
  research: "Research",
};

/** Map of known tab query param values to display names (for pages like Settings) */
const TAB_LABELS: Record<string, string> = {
  profile: "User Profile",
  account: "Account Details",
  security: "Security",
  password: "Password",
  mfa: "Multi-Factor Auth",
  sessions: "Active Sessions",
  org: "Organization",
  team: "Team Members",
  api_keys: "API Keys",
  billing: "Billing & Plans",
  llm: "LLM Providers",
  mcp: "MCP Servers",
  integrations: "Integrations",
  environment: "Environment Rules",
  preferences: "Preferences",
  notifications: "Notifications",
  appearance: "Appearance",
  delete_account: "Delete Account",
};

/** Known standalone routes that logically belong under a parent section */
const ROUTE_HIERARCHY: Record<string, { parentLabel: string; parentHref: string; subLabel: string }> = {
  "api-keys": { parentLabel: "Settings", parentHref: "/settings?tab=api_keys", subLabel: "API Keys" },
  billing: { parentLabel: "Settings", parentHref: "/settings?tab=billing", subLabel: "Billing & Plans" },
};

export function DashboardHeader() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [isProfileOpen, setIsProfileOpen] = React.useState(false);
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();

  // Build breadcrumb segments: parent + optional sub-item
  const pathSegments = pathname.split("/").filter(Boolean);
  const topSegment = pathSegments[0] ?? "overview";

  // Check if this route has an explicit parent hierarchy override
  let parentLabel = PATH_LABELS[topSegment] ?? (topSegment.charAt(0).toUpperCase() + topSegment.slice(1));
  let parentHref = `/${topSegment}`;
  let subLabel: string | null = null;

  if (ROUTE_HIERARCHY[topSegment]) {
    parentLabel = ROUTE_HIERARCHY[topSegment].parentLabel;
    parentHref = ROUTE_HIERARCHY[topSegment].parentHref;
    subLabel = ROUTE_HIERARCHY[topSegment].subLabel;
  } else if (topSegment === "settings") {
    // Inside Settings, always show active section/tab context
    const tabParam = searchParams.get("tab") || "profile";
    subLabel = TAB_LABELS[tabParam] ?? (tabParam.charAt(0).toUpperCase() + tabParam.slice(1));
  } else {
    // Check if there are deeper path segments or a ?tab= param
    const tabParam = searchParams.get("tab");
    const subPathSegment = pathSegments[1]; // e.g. /sessions/[id]
    if (tabParam) {
      subLabel = TAB_LABELS[tabParam] ?? (tabParam.charAt(0).toUpperCase() + tabParam.slice(1));
    } else if (subPathSegment) {
      subLabel = PATH_LABELS[subPathSegment] ?? (subPathSegment.charAt(0).toUpperCase() + subPathSegment.slice(1));
    }
  }

  // Back/forward navigation (browser history tracking)
  const [canGoBack, setCanGoBack] = React.useState(false);
  const [canGoForward, setCanGoForward] = React.useState(false);
  const historyStackRef = React.useRef<string[]>([]);
  const currentIndexRef = React.useRef<number>(-1);

  React.useEffect(() => {
    if (typeof window === "undefined") return;

    const queryString = searchParams.toString();
    const fullUrl = queryString ? `${pathname}?${queryString}` : pathname;
    const stack = historyStackRef.current;
    const currIdx = currentIndexRef.current;

    if (currIdx >= 0 && currIdx < stack.length && stack[currIdx] === fullUrl) {
      return;
    }

    if (currIdx > 0 && stack[currIdx - 1] === fullUrl) {
      currentIndexRef.current = currIdx - 1;
    } else if (currIdx < stack.length - 1 && stack[currIdx + 1] === fullUrl) {
      currentIndexRef.current = currIdx + 1;
    } else {
      const newStack = stack.slice(0, currIdx + 1);
      newStack.push(fullUrl);
      historyStackRef.current = newStack;
      currentIndexRef.current = newStack.length - 1;
    }

    const idx = currentIndexRef.current;
    setCanGoBack(idx > 0 || window.history.length > 1);
    setCanGoForward(idx < historyStackRef.current.length - 1);
  }, [pathname, searchParams]);

  const handleBack = () => {
    if (typeof window !== "undefined") {
      window.history.back();
    }
  };

  const handleForward = () => {
    if (typeof window !== "undefined") {
      window.history.forward();
    }
  };

  const { isMainSidebarOpen, toggleMainSidebar } = useSidebarStore();
  const { environmentMode, setEnvironmentMode, credentialsStatus } = usePlaygroundStore();

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

      {/* Desktop Sidebar Toggle Button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleMainSidebar}
        className="hidden lg:flex h-8 w-8 text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720] transition-colors"
        title={isMainSidebarOpen ? "Collapse Sidebar (Ctrl+B)" : "Expand Sidebar (Ctrl+B)"}
        aria-label="Toggle Sidebar"
      >
        {isMainSidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
      </Button>

      {/* Back / Forward Navigation Arrows */}
      <div className="hidden sm:flex items-center gap-0.5">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleBack}
          className={`h-7 w-7 transition-all duration-150 ${
            canGoBack
              ? "text-[#F5F7FA] hover:bg-[#111720] hover:text-[#22D3EE]"
              : "text-[#667085] opacity-40 hover:opacity-80 hover:bg-[#111720]"
          }`}
          title="Go back (Alt+Left)"
          aria-label="Navigate back"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleForward}
          className={`h-7 w-7 transition-all duration-150 ${
            canGoForward
              ? "text-[#F5F7FA] hover:bg-[#111720] hover:text-[#22D3EE]"
              : "text-[#667085] opacity-40 hover:opacity-80 hover:bg-[#111720]"
          }`}
          title="Go forward (Alt+Right)"
          aria-label="Navigate forward"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Separator for Mobile */}
      <div className="h-5 w-px bg-[#202833] lg:hidden" aria-hidden="true" />

      {/* Breadcrumb Area */}
      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <div className="flex flex-1 items-center space-x-2 text-xs font-mono min-w-0">
          {/* ASEP root — always points to /overview for logged-in users */}
          <Link href="/overview" className="text-[#667085] hover:text-[#F5F7FA] transition-colors shrink-0">ASEP</Link>
          <span className="text-[#667085] shrink-0">/</span>

          {/* Parent page label */}
          {subLabel ? (
            <Link href={parentHref} className="text-[#9CA6B5] hover:text-[#F5F7FA] transition-colors shrink-0">
              {parentLabel}
            </Link>
          ) : (
            <span className="text-[#F5F7FA] font-semibold tracking-wide">{parentLabel}</span>
          )}

          {/* Sub-item label (tab or nested route) */}
          {subLabel && (
            <>
              <span className="text-[#667085] shrink-0">/</span>
              <span className="text-[#F5F7FA] font-semibold tracking-wide truncate">{subLabel}</span>
            </>
          )}

          <div className="relative group shrink-0 ml-2">
            <button 
              onClick={() => {
                if (environmentMode === 'local') {
                  const mockEntries = Object.entries(credentialsStatus).filter(([, v]) => v === 'mock');
                  const mockCount = mockEntries.length;
                  if (mockCount > 0) {
                    const keysNeeded = mockEntries.map(([k]) => k).join(', ');
                    if (confirm(`Deploy Mode Activation:\n\n${mockCount} local mocks will be replaced with real services.\nKeys needed: ${keysNeeded}\n\nYou will be prompted for LIVE keys during deployment.\n\nProceed?`)) {
                      setEnvironmentMode('deploy');
                    }
                  } else {
                    setEnvironmentMode('deploy');
                  }
                } else {
                  setEnvironmentMode('local');
                }
              }}
              className={`px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase transition-colors cursor-pointer border ${environmentMode === 'local' ? 'bg-[#22D3EE]/10 text-[#22D3EE] border-[#22D3EE]/20 hover:bg-[#22D3EE]/20' : 'bg-[#F05252]/10 text-[#F05252] border-[#F05252]/20 hover:bg-[#F05252]/20'}`}
              title="Click to toggle environment mode"
            >
              [{environmentMode}]
            </button>
          </div>
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
