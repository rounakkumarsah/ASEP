"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { UpgradeModal } from "../monetization/upgrade-modal";
import { apiClient } from "@/lib/api/client";

interface LayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: LayoutProps) {
  const pathname = usePathname();
  const [isUpgradeOpen, setIsUpgradeOpen] = useState(false);
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

  const navItems = [
    { name: "Research", href: "/research", icon: "🔍" },
    { name: "Developer Copilot", href: "/copilot", icon: "🤖" },
    { name: "Knowledge Base", href: "/knowledge", icon: "📚" },
    { name: "Dashboard", href: "/dashboard", icon: "📊" },
    { name: "Billing", href: "/billing", icon: "💳" },
    { name: "Settings", href: "/settings", icon: "⚙️" },
  ];

  return (
    <div className="min-h-screen flex bg-zinc-950 text-zinc-100 font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/50 flex flex-col justify-between p-4">
        <div>
          <div className="flex items-center space-x-3 mb-8 px-2">
            <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg">
              A
            </div>
            <div>
              <h1 className="font-bold text-sm text-zinc-100">ASEP Platform</h1>
              <p className="text-xs text-zinc-400">Autonomous Engineering</p>
            </div>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                      : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-3 rounded-xl bg-zinc-950 border border-zinc-800">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-zinc-400">Current Plan:</span>
            <span className="font-semibold text-amber-400 bg-amber-950/40 border border-amber-800/50 px-2 py-0.5 rounded uppercase">
              {quota.tier}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
            <span>Daily Quota:</span>
            <span className="font-medium text-zinc-200">
              {quota.tier.toLowerCase() === "free" ? `${quota.remaining} / ${quota.limit} Left` : "Unlimited"}
            </span>
          </div>
          <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden mb-3">
            <div
              className="bg-blue-500 h-full transition-all duration-300"
              style={{
                width: quota.tier.toLowerCase() === "free" ? `${Math.min(100, Math.max(0, (quota.remaining / quota.limit) * 100))}%` : "100%",
              }}
            />
          </div>
          <button
            onClick={() => setIsUpgradeOpen(true)}
            className="w-full py-1.5 px-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold transition"
          >
            Upgrade to Pro
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 border-b border-zinc-800 px-6 flex items-center justify-between bg-zinc-900/30">
          <div className="text-sm font-medium text-zinc-300">
            {navItems.find((i) => i.href === pathname)?.name || "Dashboard"}
          </div>
          <div className="flex items-center space-x-4">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800/50">
              ● System Online
            </span>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-6 overflow-y-auto">{children}</main>
      </div>

      <UpgradeModal isOpen={isUpgradeOpen} onClose={() => setIsUpgradeOpen(false)} />
    </div>
  );
}
