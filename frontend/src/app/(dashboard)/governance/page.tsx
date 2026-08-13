"use client";

import * as React from "react";
import {
  useApprovals,
  usePolicies,
  useAudits,
} from "@/lib/api/hooks/use-governance";
import { GovernanceFilterBar } from "@/components/dashboard/governance/governance-filter-bar";
import { ApprovalCard } from "@/components/dashboard/governance/approval-card";
import { PolicyTable } from "@/components/dashboard/governance/policy-table";
import { AuditTable } from "@/components/dashboard/governance/audit-table";
import {
  Loader2,
  ShieldCheck,
  ClipboardList,
  BookOpen,
  Fingerprint,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AnimatedModal, ModalHeader, ModalTitle, ModalDescription, ModalContent, ModalFooter } from "@/components/ui/animated-modal";

type GovernanceTab =
  "overview" | "approvals" | "policies" | "authorization" | "audit";

const TABS: { id: GovernanceTab; label: string; icon: React.ReactNode }[] = [
  {
    id: "overview",
    label: "Overview",
    icon: <ShieldCheck className="w-4 h-4 mr-2" />,
  },
  {
    id: "approvals",
    label: "Approval Queue",
    icon: <ClipboardList className="w-4 h-4 mr-2" />,
  },
  {
    id: "policies",
    label: "Policy Explorer",
    icon: <BookOpen className="w-4 h-4 mr-2" />,
  },
  {
    id: "authorization",
    label: "Runtime Authorization",
    icon: <ShieldCheck className="w-4 h-4 mr-2" />,
  },
  {
    id: "audit",
    label: "Audit Summary",
    icon: <Fingerprint className="w-4 h-4 mr-2" />,
  },
];

export default function GovernanceWorkspacePage() {
  const [activeTab, setActiveTab] = React.useState<GovernanceTab>("approvals");
  const [isNewPolicyOpen, setIsNewPolicyOpen] = React.useState(false);

  const approvalsQuery = useApprovals();
  const policiesQuery = usePolicies();
  const auditsQuery = useAudits();

  const renderContent = () => {
    if (activeTab === "overview") {
      return (
        <div className="pt-10">
          <GlobalEmptyState
            icon={ShieldCheck}
            title="Activate Governance Telemetry"
            description="Monitor active security policy compliance, pending human review queues, and system privilege elevations in one place."
            action={
              <Button onClick={() => alert("Governance telemetry will automatically start logging when agent workspaces execute workflows.")} className="font-semibold">
                Configure Governance
              </Button>
            }
          />
        </div>
      );
    }

    if (activeTab === "authorization") {
      return (
        <div className="pt-10">
          <GlobalEmptyState
            icon={ShieldCheck}
            title="Define Access Policies"
            description="Restrict agent operations using granular policy rule-sets. Set up default safety rails for autonomous actions."
            action={
              <Button onClick={() => setIsNewPolicyOpen(true)} className="font-semibold bg-[#2DD4A3] text-[#090B0F] hover:bg-[#2DD4A3]/80">
                Create Policy Rule
              </Button>
            }
          />
        </div>
      );
    }

    if (activeTab === "approvals") {
      const { data, isLoading, isError, refetch } = approvalsQuery;
      const items = data?.items || [];

      if (isLoading) return <LoadingState text="Fetching approval queue..." />;
      if (isError) return <ErrorState onRetry={refetch} />;
      if (items.length === 0)
        return <EmptyStateWrapper text="No pending approvals found." />;

      return (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pb-10">
          {items.map((item) => (
            <ApprovalCard key={item.id} approval={item} />
          ))}
        </div>
      );
    }

    if (activeTab === "policies") {
      const { data, isLoading, isError, refetch } = policiesQuery;
      const items = data?.items || [];

      if (isLoading)
        return <LoadingState text="Loading governance policies..." />;
      if (isError) return <ErrorState onRetry={refetch} />;
      if (items.length === 0) return <EmptyStateWrapper text="No policies defined." />;

      return (
        <div className="pb-10 w-full max-w-5xl mx-auto">
          <PolicyTable policies={items} />
        </div>
      );
    }

    if (activeTab === "audit") {
      const { data, isLoading, isError, refetch } = auditsQuery;
      const items = data?.items || [];

      if (isLoading) return <LoadingState text="Retrieving audit logs..." />;
      if (isError) return <ErrorState onRetry={refetch} />;
      if (items.length === 0)
        return <EmptyStateWrapper text="No audit records available." />;

      return (
        <div className="pb-10 w-full max-w-5xl mx-auto">
          <AuditTable audits={items} />
        </div>
      );
    }

    return null;
  };

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Governance & Approval
          </h1>
          <p className="text-muted-foreground mt-1">
            Enforce security boundaries, approve agent actions, and audit system
            behavior.
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
                  ${
                    activeTab === tab.id
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                  }
                `}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 min-h-[400px]">{renderContent()}</div>
      </div>

      <AnimatedModal isOpen={isNewPolicyOpen} onClose={() => setIsNewPolicyOpen(false)}>
        <ModalHeader>
          <ModalTitle>Create New Policy Rule</ModalTitle>
          <ModalDescription>Define boundaries and constraints for autonomous agent actions.</ModalDescription>
        </ModalHeader>
        <ModalContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[#F5F7FA]">Policy Name</label>
            <input 
              type="text" 
              className="w-full bg-[#090B0F] border border-[#202833] rounded-md px-3 py-2 text-sm text-[#F5F7FA] focus:outline-none focus:border-[#22D3EE] transition-colors"
              placeholder="e.g. Restrict Production DB Access"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-[#F5F7FA]">Risk Threshold</label>
            <select className="w-full bg-[#090B0F] border border-[#202833] rounded-md px-3 py-2 text-sm text-[#F5F7FA] focus:outline-none focus:border-[#22D3EE] transition-colors">
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
              <option>Critical</option>
            </select>
          </div>
        </ModalContent>
        <ModalFooter>
          <Button variant="outline" onClick={() => setIsNewPolicyOpen(false)} className="border-[#202833] bg-transparent text-[#F5F7FA] hover:bg-[#202833]">
            Cancel
          </Button>
          <Button onClick={() => setIsNewPolicyOpen(false)} className="bg-[#2DD4A3] text-[#090B0F] hover:bg-[#2DD4A3]/80 font-semibold">
            Save Policy
          </Button>
        </ModalFooter>
      </AnimatedModal>
    </div>
  );
}

function LoadingState({ text }: { text: string }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg py-20">
      <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
      <p>{text}</p>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center text-destructive border border-destructive/20 bg-destructive/5 rounded-lg py-20">
      <p className="font-medium mb-4">
        Failed to connect to governance services.
      </p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Retry Connection
      </Button>
    </div>
  );
}

import { EmptyState as GlobalEmptyState } from "@/components/ui/empty-state";

function EmptyStateWrapper({ text }: { text: string }) {
  return (
    <GlobalEmptyState
      icon={ShieldCheck}
      title="No Records Found"
      description={text}
    />
  );
}
