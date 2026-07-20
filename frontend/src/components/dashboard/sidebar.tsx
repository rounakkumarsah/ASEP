"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Hexagon } from "lucide-react";
import {
  Home,
  FolderKanban,
  Activity,
  Bot,
  Database,
  BookOpen,
  ShieldCheck,
  CheckCircle2,
  BarChart3,
  Gauge,
  ClipboardList,
  Settings,
} from "lucide-react";

const navigationGroups = [
  {
    name: "Core",
    items: [
      { name: "Overview", href: "/overview", icon: Home },
      { name: "Projects", href: "/projects", icon: FolderKanban },
      { name: "Sessions", href: "/sessions", icon: Activity },
      { name: "Playground", href: "/playground", icon: Bot },
    ],
  },
  {
    name: "Intelligence",
    items: [
      { name: "Memory", href: "/memory", icon: Database },
      { name: "Knowledge", href: "/knowledge", icon: BookOpen },
    ],
  },
  {
    name: "Operations",
    items: [
      { name: "Governance", href: "/governance", icon: ShieldCheck },
      { name: "Approvals", href: "/approvals", icon: CheckCircle2 },
    ],
  },
  {
    name: "Observability",
    items: [
      { name: "Evaluation", href: "/evaluation", icon: BarChart3 },
      { name: "Metrics", href: "/metrics", icon: Gauge },
      { name: "Audit", href: "/audit", icon: ClipboardList },
    ],
  },
  {
    name: "System",
    items: [{ name: "Settings", href: "/settings", icon: Settings }],
  },
];

export function SidebarNav({ onClick }: { onClick?: () => void }) {
  const pathname = usePathname();

  return (
    <div className="flex flex-col space-y-6 h-full">
      {/* Brand */}
      <div className="px-6 py-4 flex items-center space-x-2">
        <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
          <Hexagon className="h-6 w-6" />
        </div>
        <span className="text-xl font-bold tracking-tight text-foreground">
          ASEP
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-4">
        {navigationGroups.map((group) => (
          <div key={group.name} className="mb-6">
            <h4 className="mb-2 px-2 text-xs font-semibold tracking-wider text-muted-foreground uppercase">
              {group.name}
            </h4>
            <nav className="flex flex-col space-y-1">
              {group.items.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={onClick}
                    className={cn(
                      "flex items-center space-x-3 rounded-md px-2 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-secondary text-secondary-foreground"
                        : "text-muted-foreground hover:bg-secondary/50 hover:text-foreground",
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-4 w-4",
                        isActive ? "text-primary" : "text-muted-foreground",
                      )}
                    />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
        ))}
      </div>
    </div>
  );
}

export function DashboardSidebar() {
  return (
    <aside className="hidden lg:flex w-64 h-screen flex-col border-r border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 fixed inset-y-0 z-30">
      <SidebarNav />
    </aside>
  );
}
