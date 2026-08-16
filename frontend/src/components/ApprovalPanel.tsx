"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { MonacoDiffViewer } from "./MonacoDiffViewer";
import { ShieldAlert, Loader2, CheckCircle, XCircle } from "lucide-react";

interface ApprovalPanelProps {
  sessionId: string;
}

interface PendingApprovalFile {
  path: string;
  original: string;
  modified: string;
  language?: string;
}

interface PendingApprovalResponse {
  approval_id: string;
  files: PendingApprovalFile[];
  risk_level: string;
  justification: string;
}

export const ApprovalPanel: React.FC<ApprovalPanelProps> = ({ sessionId }) => {
  const [loading, setLoading] = useState(true);
  const [pendingApproval, setPendingApproval] = useState<PendingApprovalResponse | null>(null);
  const [actionStatus, setActionStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const fetchPendingApprovals = useCallback(async () => {
    try {
      const response = await fetch(`/api/v1/sessions/${sessionId}/approvals/pending`);
      if (response.ok) {
        const data = await response.json();
        // If there are files pending, set them
        if (data && data.approval_id) {
          setPendingApproval(data);
        } else {
          setPendingApproval(null);
        }
      } else {
        setPendingApproval(null);
      }
    } catch (err) {
      console.error("Error fetching approvals:", err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchPendingApprovals();
    const interval = setInterval(fetchPendingApprovals, 5000);
    return () => clearInterval(interval);
  }, [fetchPendingApprovals]);

  const handleResolve = async (path: string, decision: "approve" | "reject") => {
    if (!pendingApproval) return;
    setActionStatus("submitting");
    setErrorMessage("");

    try {
      const response = await fetch(
        `/api/v1/sessions/${sessionId}/approvals/${pendingApproval.approval_id}/resolve`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            path,
            decision,
          }),
        }
      );

      if (response.ok) {
        setActionStatus("success");
        // Refetch immediately to clear or show next
        await fetchPendingApprovals();
      } else {
        const errData = await response.json();
        setErrorMessage(errData.detail || "Failed to submit review resolution.");
        setActionStatus("error");
      }
    } catch (err) {
      console.error("Error resolving approval:", err);
      setErrorMessage("Network error resolving review.");
      setActionStatus("error");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin text-primary mr-3" />
        <span>Loading pending approvals...</span>
      </div>
    );
  }

  if (!pendingApproval) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center p-8 text-center">
          <CheckCircle className="h-10 w-10 text-emerald-500 mb-3" />
          <h3 className="font-semibold text-foreground">All Clear</h3>
          <p className="text-xs text-muted-foreground max-w-sm mt-1">
            No actions awaiting manual confirmation or security review for this run session.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Risk Alert Header Banner */}
      <div className="flex items-start gap-4 p-4 border border-amber-500/20 bg-amber-500/5 rounded-lg text-amber-500">
        <ShieldAlert className="h-5 w-5 mt-0.5 shrink-0" />
        <div className="space-y-1">
          <h4 className="font-semibold text-sm">
            Manual Review Requested ({pendingApproval.risk_level} Risk)
          </h4>
          <p className="text-xs text-muted-foreground leading-relaxed">
            <span className="font-semibold text-foreground">Justification:</span>{" "}
            {pendingApproval.justification}
          </p>
        </div>
      </div>

      {errorMessage && (
        <div className="flex items-center gap-3 p-3 border border-destructive/20 bg-destructive/5 rounded-lg text-destructive text-xs">
          <XCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Side-by-side Diff Viewer */}
      <div className="relative">
        {actionStatus === "submitting" && (
          <div className="absolute inset-0 bg-[#090B0F]/70 z-50 flex items-center justify-center backdrop-blur-sm rounded-lg">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        )}
        <MonacoDiffViewer
          files={pendingApproval.files}
          onApprove={(path) => handleResolve(path, "approve")}
          onReject={(path) => handleResolve(path, "reject")}
        />
      </div>
    </div>
  );
};
