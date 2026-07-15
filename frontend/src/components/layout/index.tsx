"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuth } from "@/lib/providers/auth-provider"
import { Button } from "@/components/ui/button"
import {
  LayoutDashboard,
  FolderOpen,
  Activity,
  Database,
  TerminalSquare,
  CheckSquare,
  BarChart,
  ShieldAlert,
  LogOut,
  Moon,
  Sun
} from "lucide-react"
import { useTheme } from "next-themes"

export function Sidebar() {
  const pathname = usePathname()
  
  const navItems = [
    { name: "Overview", href: "/overview", icon: LayoutDashboard },
    { name: "Projects", href: "/projects", icon: FolderOpen },
    { name: "Sessions", href: "/sessions", icon: Activity },
    { name: "Knowledge", href: "/knowledge", icon: Database },
    { name: "Playground", href: "/playground", icon: TerminalSquare },
    { name: "Approvals", href: "/approvals", icon: CheckSquare },
    { name: "Metrics", href: "/metrics", icon: BarChart },
    { name: "Audit Log", href: "/audit", icon: ShieldAlert },
  ]

  return (
    <div className="flex h-screen w-64 flex-col border-r bg-card text-card-foreground">
      <div className="flex h-14 items-center border-b px-4">
        <span className="text-lg font-bold tracking-tight">ASEP Platform</span>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link key={item.name} href={item.href}>
              <Button
                variant={isActive ? "secondary" : "ghost"}
                className="w-full justify-start"
              >
                <item.icon className="mr-2 h-4 w-4" />
                {item.name}
              </Button>
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

export function Header() {
  const { user, logout } = useAuth()
  const { theme, setTheme } = useTheme()

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div className="flex items-center">
        {/* Breadcrumbs could go here */}
        <h2 className="text-sm font-medium">Dashboard</h2>
      </div>
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
        <div className="flex items-center space-x-2 text-sm">
          <span className="font-medium">{user?.username}</span>
          <span className="rounded-full bg-secondary px-2 py-1 text-xs">
            {user?.role}
          </span>
        </div>
        <Button variant="outline" size="sm" onClick={logout}>
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </Button>
      </div>
    </header>
  )
}
