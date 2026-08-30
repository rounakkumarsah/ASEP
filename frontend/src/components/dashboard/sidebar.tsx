"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { apiClient } from "@/lib/api/client";
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
  Cpu,
  ExternalLink,
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
    items: [
      { name: "Settings", href: "/settings", icon: Settings },
      { name: "Documentation", href: "/documentation", icon: BookOpen, external: true },
    ],
  },
];

export function SidebarNav({ onClick }: { onClick?: () => void }) {
  const pathname = usePathname();
  const [quota, setQuota] = useState<{ tier: string; limit: number; used: number; remaining: number }>({
    tier: "free",
    limit: 10,
    used: 0,
    remaining: 10,
  });

  useEffect(() => {
    let isMounted = true;
    apiClient
      .get("/api/v1/users/quota")
      .then((res) => {
        if (isMounted && res.data) {
          setQuota({
            tier: res.data.tier || "free",
            limit: res.data.limit ?? 10,
            used: res.data.used ?? 0,
            remaining: res.data.remaining ?? 10,
          });
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, [pathname]);

  return (
    <div className="flex flex-col h-full bg-[#0D1117] text-[#F5F7FA]">
      {/* Brand Header */}
      <div className="px-5 py-4 border-b border-[#202833] flex items-center">
        <Link href="/overview" className="flex items-center space-x-2.5 group">
          <div className="p-1.5 rounded-md bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/40 transition-colors">
            <Cpu className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-wider uppercase font-mono text-[#F5F7FA]">
              ASEP
            </span>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] text-[#9CA6B5] font-mono tracking-tight">
                v0.1.0 • Control Plane
              </span>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[8px] font-mono font-medium bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/20">
                PROD
              </span>
            </div>
          </div>
        </Link>
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
                const isExternal = (item as { external?: boolean }).external;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={onClick}
                    target={isExternal ? "_blank" : undefined}
                    rel={isExternal ? "noopener noreferrer" : undefined}
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
                    {isExternal && <ExternalLink className="h-3 w-3 text-[#667085] group-hover:text-[#9CA6B5]" />}
                  </Link>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Quota Box */}
      <div className="px-4 pb-4 shrink-0">
        <div className="p-3 rounded-xl bg-[#111720] border border-[#202833]">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-[#9CA6B5]">Current Plan:</span>
            <span className="font-semibold font-mono bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/20 px-2 py-0.5 rounded uppercase text-[10px]">
              {quota.tier}
            </span>
          </div>
          <div className="flex items-center justify-between text-[#9CA6B5] mb-2 font-mono text-[10px]">
            <span>Daily Quota:</span>
            <span className="font-bold text-[#F5F7FA]">
              {quota.tier.toLowerCase() === "free" ? `${quota.remaining} / ${quota.limit} Left` : "Unlimited"}
            </span>
          </div>
          {quota.tier.toLowerCase() === "free" && (
            <div className="h-1.5 w-full bg-[#090B0F] rounded-full overflow-hidden mb-3">
              <div
                className="h-full bg-[#22D3EE] rounded-full"
                style={{ width: `${Math.max(0, (quota.used / quota.limit) * 100)}%` }}
              />
            </div>
          )}
          <Link
            href="/pricing"
            className="block w-full py-1.5 px-3 text-center rounded-lg bg-[#22D3EE] hover:bg-[#67E8F9] transition text-xs font-bold text-[#090B0F] shadow-md shadow-[#22D3EE]/10"
          >
            Upgrade to Pro
          </Link>
        </div>
      </div>

      {/* Footer System Status */}
      <div className="px-4 py-3 border-t border-[#202833] bg-[#090B0F] flex items-center justify-between text-[11px] font-mono text-[#9CA6B5] shrink-0">
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
