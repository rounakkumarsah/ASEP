"use client"

import * as React from "react"
import { useApprovals, usePolicies, useAudits } from "@/lib/api/hooks/use-governance"
import { GovernanceFilterBar } from "@/components/dashboard/governance/governance-filter-bar"
import { ApprovalCard } from "@/components/dashboard/governance/approval-card"
import { PolicyCard } from "@/components/dashboard/governance/policy-card"
import { AuditCard } from "@/components/dashboard/governance/audit-card"
import { Loader2, ShieldCheck, ClipboardList, BookOpen, Fingerprint } from "lucide-react"
import { Button } from "@/components/ui/button"

type GovernanceTab = "overview" | "approvals" | "policies" | "authorization" | "audit"

const TABS: { id: GovernanceTab; label: string; icon: React.ReactNode }[] = [
  { id: "overview", label: "Overview", icon: <ShieldCheck className="w-4 h-4 mr-2" /> },
  { id: "approvals", label: "Approval Queue", icon: <ClipboardList className="w-4 h-4 mr-2" /> },
  { id: "policies", label: "Policy Explorer", icon: <BookOpen className="w-4 h-4 mr-2" /> },
  { id: "authorization", label: "Runtime Authorization", icon: <ShieldCheck className="w-4 h-4 mr-2" /> },
  { id: "audit", label: "Audit Summary", icon: <Fingerprint className="w-4 h-4 mr-2" /> },
]

export default function GovernanceWorkspacePage() {
  const [activeTab, setActiveTab] = React.useState<GovernanceTab>("approvals")

  const approvalsQuery = useApprovals()
  const policiesQuery = usePolicies()
  const auditsQuery = useAudits()

  const renderContent = () => {
    if (activeTab === "overview" || activeTab === "authorization") {
      return (
        <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
          <ShieldCheck className="h-10 w-10 text-muted-foreground mb-4" />
          <h3 className="font-semibold text-foreground text-lg">Coming Soon</h3>
          <p className="text-sm mt-1 max-w-sm text-center">
            The {activeTab} panel is scheduled for a future architectural phase.
          </p>
        </div>
      )
    }

    if (activeTab === "approvals") {
      const { data, isLoading, isError, refetch } = approvalsQuery
      const items = data?.items || []

      if (isLoading) return <LoadingState text="Fetching approval queue..." />
      if (isError) return <ErrorState onRetry={refetch} />
      if (items.length === 0) return <EmptyState text="No pending approvals found." />

      return (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pb-10">
          {items.map(item => <ApprovalCard key={item.id} approval={item} />)}
        </div>
      )
    }

    if (activeTab === "policies") {
      const { data, isLoading, isError, refetch } = policiesQuery
      const items = data?.items || []

      if (isLoading) return <LoadingState text="Loading governance policies..." />
      if (isError) return <ErrorState onRetry={refetch} />
      if (items.length === 0) return <EmptyState text="No policies defined." />

      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-10">
          {items.map(item => <PolicyCard key={item.id} policy={item} />)}
        </div>
      )
    }

    if (activeTab === "audit") {
      const { data, isLoading, isError, refetch } = auditsQuery
      const items = data?.items || []

      if (isLoading) return <LoadingState text="Retrieving audit logs..." />
      if (isError) return <ErrorState onRetry={refetch} />
      if (items.length === 0) return <EmptyState text="No audit records available." />

      return (
        <div className="flex flex-col gap-3 pb-10">
          {items.map(item => <AuditCard key={item.id} audit={item} />)}
        </div>
      )
    }

    return null
  }

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Governance & Approval</h1>
          <p className="text-muted-foreground mt-1">
            Enforce security boundaries, approve agent actions, and audit system behavior.
          </p>
        </div>
      </div>

      <GovernanceFilterBar />

      <div className="flex flex-col flex-1 gap-6 pt-2">
        <div className="border-b border-border w-full">
          <nav className="-mb-px flex space-x-6 overflow-x-auto pb-1">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id 
                    ? 'border-primary text-primary' 
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                  }
                `}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 min-h-[400px]">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}

function LoadingState({ text }: { text: string }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
      <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
      <p>{text}</p>
    </div>
  )
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg py-20">
      <p className="font-medium mb-4">Failed to connect to governance services.</p>
      <Button variant="outline" size="sm" onClick={onRetry}>Retry Connection</Button>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
      <div className="bg-muted h-12 w-12 rounded-full flex items-center justify-center mb-4">
        <ShieldCheck className="h-6 w-6 text-muted-foreground" />
      </div>
      <h3 className="font-semibold text-foreground">No Records</h3>
      <p className="text-sm mt-1">{text}</p>
    </div>
  )
}
