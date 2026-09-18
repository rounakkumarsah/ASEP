"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useSearchParams, useRouter } from "next/navigation";
import { 
  Menu, 
  Search, 
  Bell, 
  User, 
  LogOut, 
  Settings as SettingsIcon, 
  PanelLeft, 
  PanelLeftClose, 
  ChevronLeft, 
  ChevronRight,
  CheckCheck,
  Trash2,
  X,
  Sparkles,
  Shield,
  Bot,
  LayoutDashboard,
  Terminal,
  Activity,
  ArrowRight,
  Database,
  BookOpen,
  Key,
  CreditCard,
  Server,
  FolderKanban,
  CheckCircle2,
  BarChart3,
  Gauge,
  ClipboardList
} from "lucide-react";
import { useSidebarStore } from "@/lib/stores/sidebarStore";

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
  billing: "Billing & Plans",
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

/** Quick-search catalog items */
interface SearchItem {
  id: string;
  title: string;
  category: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const SEARCH_ITEMS: SearchItem[] = [
  { id: "overview", title: "Overview", category: "Control Plane", description: "Cluster health, running agents & telemetry", href: "/overview", icon: LayoutDashboard },
  { id: "projects", title: "Projects", category: "Control Plane", description: "Workspace repositories & branch manager", href: "/projects", icon: FolderKanban },
  { id: "playground", title: "Playground", category: "Control Plane", description: "Multi-agent coding environment & live REPL", href: "/playground", icon: Bot },
  { id: "sessions", title: "Sessions", category: "Orchestration", description: "Execution traces, state logs & run history", href: "/sessions", icon: Activity },
  { id: "memory", title: "Memory", category: "Orchestration", description: "Episodic & semantic agent vector memory", href: "/memory", icon: Database },
  { id: "knowledge", title: "Knowledge", category: "Orchestration", description: "Indexed codebases & document embeddings", href: "/knowledge", icon: BookOpen },
  { id: "skills", title: "Skills", category: "Orchestration", description: "Installed tools, MCP capabilities & skills", href: "/skills", icon: Sparkles },
  { id: "governance", title: "Governance", category: "Governance", description: "Zero-trust sandbox policies & safety filters", href: "/governance", icon: Shield },
  { id: "approvals", title: "Approvals", category: "Governance", description: "Human-in-the-loop pending authorizations", href: "/approvals", icon: CheckCircle2 },
  { id: "evaluation", title: "Evaluation", category: "Observability", description: "Regression benchmarks & accuracy scores", href: "/evaluation", icon: BarChart3 },
  { id: "metrics", title: "Metrics", category: "Observability", description: "Latency, compute load & token telemetry", href: "/metrics", icon: Gauge },
  { id: "audit", title: "Audit Logs", category: "Observability", description: "Cryptographic signature logs & action trail", href: "/audit", icon: ClipboardList },
  { id: "settings", title: "System Settings", category: "Settings", description: "Platform preferences, credentials & options", href: "/settings", icon: SettingsIcon },
  { id: "profile", title: "User Profile", category: "Settings", description: "Display name, username & personal identity", href: "/settings?tab=profile", icon: User },
  { id: "security", title: "Security & MFA", category: "Settings", description: "Password, two-factor auth & active sessions", href: "/settings?tab=security", icon: Shield },
  { id: "api-keys", title: "API Keys", category: "Settings", description: "Secret authentication keys & API tokens", href: "/settings?tab=api_keys", icon: Key },
  { id: "billing", title: "Billing & Plans", category: "Settings", description: "Usage quotas, plan tier & subscription", href: "/settings?tab=billing", icon: CreditCard },
  { id: "llm", title: "LLM Providers", category: "Settings", description: "OpenAI, Anthropic & Gemini provider keys", href: "/settings?tab=llm", icon: Sparkles },
  { id: "mcp", title: "MCP Servers", category: "Settings", description: "Configure Model Context Protocol endpoints", href: "/settings?tab=mcp", icon: Server },
  { id: "docs", title: "Documentation", category: "System", description: "Architecture guides, API docs & tutorials", href: "/documentation", icon: BookOpen },
];

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  type: "success" | "info" | "warning";
  read: boolean;
}

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "n1",
    title: "Agent Supervisor Online",
    message: "LangGraph autonomous agent swarm ready for instructions.",
    time: "Just now",
    type: "success",
    read: false,
  },
  {
    id: "n2",
    title: "Zero-Trust Sandbox Enforced",
    message: "Network egress and safe tool policy filters actively running.",
    time: "12m ago",
    type: "info",
    read: false,
  },
  {
    id: "n3",
    title: "System Cluster Healthy",
    message: "99.9% uptime reported across all backend execution pods.",
    time: "45m ago",
    type: "success",
    read: false,
  },
  {
    id: "n4",
    title: "Daily Quota Active",
    message: "Free tier active: 10 daily agent runs available for your workspace.",
    time: "2h ago",
    type: "info",
    read: false,
  },
];

export function DashboardHeader() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [isProfileOpen, setIsProfileOpen] = React.useState(false);
  const [isSearchOpen, setIsSearchOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedSearchIndex, setSelectedSearchIndex] = React.useState(0);
  const [isNotificationsOpen, setIsNotificationsOpen] = React.useState(false);
  const [notifications, setNotifications] = React.useState<NotificationItem[]>(INITIAL_NOTIFICATIONS);

  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, logout } = useAuth();
  const searchInputRef = React.useRef<HTMLInputElement>(null);

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

  // Keyboard shortcut for Command Palette (Ctrl+K or Cmd+K)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
      if (e.key === "Escape") {
        setIsSearchOpen(false);
        setIsNotificationsOpen(false);
        setIsProfileOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Autofocus search input on open
  React.useEffect(() => {
    if (isSearchOpen) {
      setTimeout(() => searchInputRef.current?.focus(), 50);
      setSelectedSearchIndex(0);
    } else {
      setSearchQuery("");
    }
  }, [isSearchOpen]);

  // Filtered search items
  const filteredSearchItems = React.useMemo(() => {
    if (!searchQuery.trim()) return SEARCH_ITEMS;
    const q = searchQuery.toLowerCase().trim();
    return SEARCH_ITEMS.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        item.category.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q)
    );
  }, [searchQuery]);

  const handleSelectSearchItem = (item: SearchItem) => {
    setIsSearchOpen(false);
    router.push(item.href);
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedSearchIndex((prev) => (prev + 1) % Math.max(1, filteredSearchItems.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedSearchIndex((prev) => (prev - 1 + filteredSearchItems.length) % Math.max(1, filteredSearchItems.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredSearchItems[selectedSearchIndex]) {
        handleSelectSearchItem(filteredSearchItems[selectedSearchIndex]);
      }
    }
  };

  // Notifications handlers
  const unreadCount = notifications.filter((n) => !n.read).length;

  const handleMarkAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const handleClearAllNotifications = () => {
    setNotifications([]);
  };

  const handleDismissNotification = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const { isMainSidebarOpen, toggleMainSidebar } = useSidebarStore();

  return (
    <>
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
          </div>

          {/* Right Actions */}
          <div className="flex items-center gap-x-1 sm:gap-x-2">
            {/* Functional Search / Command Palette Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsSearchOpen(true)}
              className="h-8 px-2 text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720] flex items-center gap-1.5 transition-colors"
              aria-label="Search pages and settings (Ctrl+K)"
              title="Search pages and settings (Ctrl+K)"
            >
              <Search className="h-4 w-4" />
              <span className="hidden md:inline text-[11px] font-mono text-[#667085]">Search...</span>
              <kbd className="hidden md:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[9px] font-mono font-medium text-[#667085] bg-[#111720] border border-[#202833] rounded">
                ⌘K
              </kbd>
            </Button>

            {/* Functional Notifications Dropdown */}
            <div className="relative">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsNotificationsOpen((prev) => !prev)}
                className="h-8 w-8 text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720] relative transition-colors"
                aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ""}`}
                title="System Notifications"
              >
                <Bell className="h-4 w-4" />
                {unreadCount > 0 && (
                  <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-[#2DD4A3] animate-pulse" />
                )}
              </Button>

              {/* Notifications Popover Dropdown */}
              {isNotificationsOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsNotificationsOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl border border-[#202833] bg-[#0D1117] text-[#F5F7FA] shadow-2xl z-50 overflow-hidden flex flex-col font-sans text-xs animate-in fade-in-0 zoom-in-95 duration-150">
                    <div className="px-4 py-3 border-b border-[#202833] flex items-center justify-between bg-[#111720]/70">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-[#F5F7FA]">Notifications</span>
                        {unreadCount > 0 && (
                          <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold rounded-full bg-[#2DD4A3]/10 text-[#2DD4A3] border border-[#2DD4A3]/30">
                            {unreadCount} new
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {unreadCount > 0 && (
                          <button
                            onClick={handleMarkAllNotificationsRead}
                            className="text-[11px] text-[#22D3EE] hover:underline flex items-center gap-1 cursor-pointer"
                            title="Mark all as read"
                          >
                            <CheckCheck className="h-3 w-3" />
                            <span>Mark read</span>
                          </button>
                        )}
                        {notifications.length > 0 && (
                          <button
                            onClick={handleClearAllNotifications}
                            className="text-[11px] text-[#667085] hover:text-[#F05252] flex items-center gap-1 cursor-pointer transition-colors"
                            title="Clear all"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="max-h-80 overflow-y-auto divide-y divide-[#202833]/60">
                      {notifications.length === 0 ? (
                        <div className="p-8 text-center text-[#667085] flex flex-col items-center gap-2">
                          <CheckCircle2 className="h-8 w-8 text-[#2DD4A3]/60" />
                          <p className="font-medium text-sm text-[#9CA6B5]">All caught up!</p>
                          <p className="text-xs">No active alerts or system notifications.</p>
                        </div>
                      ) : (
                        notifications.map((item) => (
                          <div
                            key={item.id}
                            onClick={() => {
                              setNotifications((prev) =>
                                prev.map((n) => (n.id === item.id ? { ...n, read: true } : n))
                              );
                            }}
                            className={`p-3.5 hover:bg-[#111720] transition-colors cursor-pointer flex items-start gap-3 relative group ${
                              !item.read ? "bg-[#111720]/40" : "opacity-80"
                            }`}
                          >
                            <span
                              className={`mt-1 h-2 w-2 rounded-full shrink-0 ${
                                !item.read ? "bg-[#2DD4A3]" : "bg-transparent"
                              }`}
                            />
                            <div className="flex-1 min-w-0 space-y-0.5">
                              <div className="flex items-center justify-between gap-2">
                                <p className={`font-semibold truncate text-xs ${!item.read ? "text-[#F5F7FA]" : "text-[#9CA6B5]"}`}>
                                  {item.title}
                                </p>
                                <span className="text-[10px] text-[#667085] font-mono shrink-0">{item.time}</span>
                              </div>
                              <p className="text-[11px] text-[#9CA6B5] line-clamp-2 leading-relaxed">{item.message}</p>
                            </div>
                            <button
                              onClick={(e) => handleDismissNotification(item.id, e)}
                              className="opacity-0 group-hover:opacity-100 text-[#667085] hover:text-[#F5F7FA] p-1 rounded transition-opacity"
                              title="Dismiss"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        ))
                      )}
                    </div>

                    <div className="p-2 border-t border-[#202833] bg-[#090B0F] text-center">
                      <span className="text-[10px] font-mono text-[#667085]">
                        System Status: Nominal • Autonomous Agent Engine
                      </span>
                    </div>
                  </div>
                </>
              )}
            </div>

            <div className="hidden sm:block h-5 w-px bg-[#202833]" aria-hidden="true" />

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

      {/* Global Quick Search / Command Palette Dialog */}
      {isSearchOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4">
          <div
            className="fixed inset-0 bg-black/80 backdrop-blur-xs transition-opacity animate-in fade-in-0"
            onClick={() => setIsSearchOpen(false)}
          />

          <div className="relative w-full max-w-xl rounded-2xl border border-[#202833] bg-[#0D1117] shadow-2xl overflow-hidden z-10 animate-in fade-in-0 zoom-in-95 duration-150">
            {/* Search Input Bar */}
            <div className="flex items-center px-4 border-b border-[#202833] bg-[#111720]/60">
              <Search className="h-4 w-4 text-[#667085] shrink-0" />
              <input
                ref={searchInputRef}
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setSelectedSearchIndex(0);
                }}
                onKeyDown={handleSearchKeyDown}
                placeholder="Search pages, commands, and settings..."
                className="w-full bg-transparent px-3 py-3.5 text-sm text-[#F5F7FA] placeholder-[#667085] focus:outline-none"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="text-[#667085] hover:text-[#F5F7FA] p-1"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
              <kbd className="ml-2 px-1.5 py-0.5 text-[10px] font-mono text-[#667085] bg-[#0D1117] border border-[#202833] rounded">
                ESC
              </kbd>
            </div>

            {/* Results List */}
            <div className="max-h-80 overflow-y-auto p-2 space-y-1">
              {filteredSearchItems.length === 0 ? (
                <div className="p-8 text-center text-[#667085]">
                  <p className="text-sm">No results found for &ldquo;{searchQuery}&rdquo;</p>
                  <p className="text-xs mt-1 text-[#667085]/80">Try searching for overview, playground, settings, or api keys.</p>
                </div>
              ) : (
                filteredSearchItems.map((item, idx) => {
                  const Icon = item.icon;
                  const isSelected = idx === selectedSearchIndex;
                  return (
                    <div
                      key={item.id}
                      onClick={() => handleSelectSearchItem(item)}
                      onMouseEnter={() => setSelectedSearchIndex(idx)}
                      className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                        isSelected
                          ? "bg-[#111720] text-[#F5F7FA] border-l-2 border-[#22D3EE] pl-2.5"
                          : "text-[#9CA6B5] hover:bg-[#111720]/60 hover:text-[#F5F7FA]"
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`p-1.5 rounded-md border ${isSelected ? "bg-[#22D3EE]/10 border-[#22D3EE]/30 text-[#22D3EE]" : "bg-[#111720] border-[#202833] text-[#667085]"}`}>
                          <Icon className="h-4 w-4 shrink-0" />
                        </div>
                        <div className="min-w-0">
                          <p className={`font-semibold text-xs truncate ${isSelected ? "text-[#F5F7FA]" : "text-[#F5F7FA]/90"}`}>
                            {item.title}
                          </p>
                          <p className="text-[11px] text-[#667085] truncate">{item.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-2">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#111720] text-[#667085] border border-[#202833]">
                          {item.category}
                        </span>
                        {isSelected && <ArrowRight className="h-3 w-3 text-[#22D3EE]" />}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer Navigation Hints */}
            <div className="px-4 py-2.5 border-t border-[#202833] bg-[#090B0F] flex items-center justify-between text-[11px] font-mono text-[#667085]">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <kbd className="px-1 py-0.5 bg-[#111720] border border-[#202833] rounded text-[9px]">↑↓</kbd> Navigate
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1 py-0.5 bg-[#111720] border border-[#202833] rounded text-[9px]">↵</kbd> Select
                </span>
                <span className="flex items-center gap-1">
                  <kbd className="px-1 py-0.5 bg-[#111720] border border-[#202833] rounded text-[9px]">ESC</kbd> Close
                </span>
              </div>
              <span className="text-[10px] text-[#22D3EE]">ASEP Quick Navigation</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
