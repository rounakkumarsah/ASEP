"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
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
  Terminal,
  Cpu
} from "lucide-react";

const navigationGroups = [
  {
    name: "Control Plane",
    items: [
      { name: "Overview", href: "/overview", icon: LayoutDashboard },
      { name: "Projects", href: "/projects", icon: FolderKanban },
      { name: "Playground", href: "/playground", icon: Bot },
      { name: "Copilot", href: "/copilot", icon: Terminal },
    ],
  },
  {
    name: "Orchestration & State",
    items: [
      { name: "Sessions", href: "/sessions", icon: Activity },
      { name: "Memory", href: "/memory", icon: Database },
      { name: "Knowledge", href: "/knowledge", icon: BookOpen },
    ],
  },
  {
    name: "Governance & Control",
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
      { name: "Audit Logs", href: "/audit", icon: ClipboardList },
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
    <div className="flex flex-col h-full bg-[#0D1117] text-[#F5F7FA]">
      {/* Brand Header */}
      <div className="px-5 py-4 border-b border-[#202833] flex items-center justify-between">
        <Link href="/overview" className="flex items-center space-x-2.5 group">
          <div className="p-1.5 rounded-md bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/40 transition-colors">
            <Cpu className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-wider uppercase font-mono text-[#F5F7FA]">
              ASEP
            </span>
            <span className="text-[10px] text-[#9CA6B5] font-mono tracking-tight">
              v0.1.0 • Control Plane
            </span>
          </div>
        </Link>
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/20">
          PROD
        </span>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navigationGroups.map((group) => (
          <div key={group.name} className="space-y-1">
            <h4 className="px-2 text-[10px] font-bold tracking-wider text-[#667085] uppercase font-mono mb-2">
              {group.name}
            </h4>
            <nav className="space-y-0.5">
              {group.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/overview" && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={onClick}
                    className={cn(
                      "flex items-center justify-between rounded-md px-2.5 py-1.5 text-xs font-medium transition-all duration-150 group outline-none",
                      isActive
                        ? "bg-[#111720] text-[#F5F7FA] border-l-2 border-[#22D3EE] pl-2 font-semibold shadow-xs"
                        : "text-[#9CA6B5] hover:text-[#F5F7FA] hover:bg-[#111720]/60",
                    )}
                  >
                    <div className="flex items-center space-x-2.5">
                      <Icon
                        className={cn(
                          "h-4 w-4 shrink-0 transition-colors",
                          isActive ? "text-[#22D3EE]" : "text-[#667085] group-hover:text-[#9CA6B5]",
                        )}
                      />
                      <span>{item.name}</span>
                    </div>
                  </Link>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Footer System Status */}
      <div className="px-4 py-3 border-t border-[#202833] bg-[#090B0F] flex items-center justify-between text-[11px] font-mono text-[#9CA6B5]">
        <div className="flex items-center space-x-2">
          <span className="h-2 w-2 rounded-full bg-[#2DD4A3] animate-pulse" />
          <span>System Healthy</span>
        </div>
        <span className="text-[10px] text-[#667085]">99.9% Uptime</span>
      </div>
    </div>
  );
}

export function DashboardSidebar() {
  return (
    <aside className="hidden lg:flex w-64 h-screen flex-col border-r border-[#202833] bg-[#0D1117] fixed inset-y-0 z-30">
      <SidebarNav />
    </aside>
  );
}
