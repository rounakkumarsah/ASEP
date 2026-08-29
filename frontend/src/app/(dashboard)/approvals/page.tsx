"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/providers/auth-provider";
import { 
  Clock, 
  Loader2, 
  AlertTriangle,
  ShieldCheck,
  User,
  Sparkles
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";

interface ReviewSession {
  session_id: string;
  tool_name: string;
  args: Record<string, unknown>;
  status: "pending" | "approved" | "rejected" | "escalated";
  decision?: string;
  notes?: string;
  reviewer?: string;
  created_at?: string;
}

interface ApprovalFile {
  path: string;
  original: string;
  modified: string;
  language?: string;
}

import { MonacoDiffViewer } from "@/components/MonacoDiffViewer";

export default function ApprovalsPage() {
  const { user } = useAuth();
  const [queue, setQueue] = React.useState<ReviewSession[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [notes, setNotes] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState<string | null>(null);
  const [activeSessionId, setActiveSessionId] = React.useState<string | null>(null);
  const [activeFiles, setActiveFiles] = React.useState<ApprovalFile[]>([]);
  const [loadingFiles, setLoadingFiles] = React.useState(false);

  const DEFAULT_DEMO_APPROVALS: ReviewSession[] = [
    {
      session_id: "sess_hitl_9021",
      tool_name: "filesystem_write",
      args: { path: "/etc/hosts", content: "127.0.0.1 custom_host" },
      status: "pending",
      notes: "Policy violation: Root directory write restriction",
      reviewer: "pending",
      created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    },
    {
      session_id: "sess_hitl_9022",
      tool_name: "network_egress",
      args: { host: "unverified-api.internal", port: 443 },
      status: "escalated",
      notes: "Policy violation: Sovereign air-gap egress boundary",
      reviewer: "pending",
      created_at: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    },
  ];

  const fetchQueue = React.useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiClient.get("/api/v1/governance/hitl/queue");
      const sessions = res.data && Array.isArray(res.data) && res.data.length > 0 ? res.data : DEFAULT_DEMO_APPROVALS;
      setQueue(sessions);
      
      const pending = sessions.filter((item: ReviewSession) => item.status === "pending" || item.status === "escalated");
      if (pending.length > 0 && !activeSessionId) {
        setActiveSessionId(pending[0].session_id);
      }
    } catch {
      setQueue(DEFAULT_DEMO_APPROVALS);
      if (!activeSessionId) {
        setActiveSessionId(DEFAULT_DEMO_APPROVALS[0].session_id);
      }
    } finally {
      setLoading(false);
    }
  }, [activeSessionId]);

  React.useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  const fetchFilesForSession = React.useCallback(async (sessId: string) => {
    setLoadingFiles(true);
    try {
      const res = await apiClient.get(`/api/v1/sessions/${sessId}/approvals/pending`);
      if (res.data && res.data.files) {
        setActiveFiles(res.data.files);
      } else {
        // Fallback mockup if no files are bound to the session yet
        setActiveFiles([
          {
            path: "main.py",
            original: "# No modifications yet\nprint('hello')",
            modified: "# Modifications added\nprint('hello world')",
          }
        ]);
      }
    } catch {
      // Mockup default values if endpoint fails
      setActiveFiles([
        {
          path: "main.py",
          original: "def execute():\n    pass",
          modified: "def execute():\n    print('Approved Execution')",
        }
      ]);
    } finally {
      setLoadingFiles(false);
    }
  }, []);

  React.useEffect(() => {
    if (activeSessionId) {
      fetchFilesForSession(activeSessionId);
    } else {
      setActiveFiles([]);
    }
  }, [activeSessionId, fetchFilesForSession]);

  const handleDecision = async (sessionId: string, action: "approve" | "reject") => {
    setSubmitting(sessionId);
    setError("");
    try {
      await apiClient.post("/api/v1/governance/hitl/review", {
        session_id: sessionId,
        action: action === "approve" ? "APPROVED" : "REJECTED",
        reviewer: user?.username || "administrator",
        role: "ADMINISTRATOR",
        notes: notes[sessionId] || ""
      });
      
      // Update local state
      setQueue(prev => prev.map(s => 
        s.session_id === sessionId 
          ? { ...s, status: action === "approve" ? "approved" : "rejected", notes: notes[sessionId] } 
          : s
      ));

      // Clear selection or select next
      setActiveSessionId(null);
      fetchQueue();
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to submit approval decision.");
    } finally {
      setSubmitting(null);
    }
  };

  const handleNoteChange = (sessionId: string, value: string) => {
    setNotes(prev => ({ ...prev, [sessionId]: value }));
  };

  if (loading) {
    return (
      <div className="h-[400px] w-full flex flex-col items-center justify-center text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p>Loading approval queue details...</p>
      </div>
    );
  }

  const pendingItems = queue.filter(item => item.status === "pending" || item.status === "escalated");
  const historyItems = queue.filter(item => item.status === "approved" || item.status === "rejected");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Human-in-the-Loop Queue</h1>
        <p className="text-muted-foreground mt-1">
          Review and authorize pending agent actions requiring governance sign-off.
        </p>
      </div>

      {error && (
        <div className="p-4 border border-destructive/20 bg-destructive/10 text-destructive text-sm rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Split Layout: Sidebar list + Diff Editor */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Column: Sidebar List of Pending Sessions */}
        <div className="space-y-4 lg:col-span-1">
          <h2 className="text-lg font-bold flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            <span>Pending Approvals ({pendingItems.length})</span>
          </h2>

          {pendingItems.length === 0 ? (
            <EmptyState
              title="No pending approvals"
              description="No tasks require manual authorization. All agents running automatically."
              icon={ShieldCheck}
            />
          ) : (
            <div className="space-y-3">
              {pendingItems.map(item => (
                <button
                  key={item.session_id}
                  onClick={() => setActiveSessionId(item.session_id)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    activeSessionId === item.session_id
                      ? "border-primary bg-primary/5 text-foreground shadow-sm"
                      : "border-border/40 hover:border-border bg-card/30 text-muted-foreground"
                  }`}
                >
                  <div className="flex justify-between items-center text-xs font-mono mb-2">
                    <span>{item.session_id.slice(0, 12)}...</span>
                    <span className="text-[10px] font-bold text-yellow-500 uppercase">Pending</span>
                  </div>
                  <h4 className="font-semibold text-foreground truncate">{item.tool_name}</h4>
                  <p className="text-xs text-muted-foreground mt-1 truncate">
                    Args: {JSON.stringify(item.args)}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Diff Editor */}
        <div className="lg:col-span-2 space-y-4">
          {activeSessionId ? (
            <Card className="border-border/40">
              <CardHeader className="border-b border-border/50 pb-4">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  <span>Interactive Review & Diff Comparison</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6 space-y-4 flex flex-col min-h-[500px]">
                {loadingFiles ? (
                  <div className="flex-1 flex flex-col items-center justify-center p-12 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
                    <span>Loading session file metrics...</span>
                  </div>
                ) : (
                  <>
                    {/* Monaco Diff Viewer */}
                    <div className="flex-1 min-h-[400px]">
                      <MonacoDiffViewer
                        files={activeFiles}
                        onApprove={() => handleDecision(activeSessionId, "approve")}
                        onReject={() => handleDecision(activeSessionId, "reject")}
                        readOnly={submitting === activeSessionId}
                      />
                    </div>

                    {/* Reviewer Comments input wrapper */}
                    <div className="space-y-2 pt-2 border-t border-border/50">
                      <label className="text-xs font-semibold text-muted-foreground uppercase">Reviewer Notes</label>
                      <Input
                        value={notes[activeSessionId] || ""}
                        onChange={e => handleNoteChange(activeSessionId, e.target.value)}
                        placeholder="Explain authorization decisions or list task changes..."
                      />
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="h-[400px] flex flex-col items-center justify-center text-muted-foreground border border-dashed rounded-lg bg-card/10">
              <AlertTriangle className="h-10 w-10 text-muted-foreground/30 mb-3" />
              <p className="text-sm font-semibold">Select a session to begin file verification</p>
            </div>
          )}
        </div>
      </div>

      {/* History Queue Section */}
      <div className="space-y-4 pt-4">
        <h2 className="text-xl font-bold flex items-center gap-2 text-muted-foreground">
          <ShieldCheck className="h-5 w-5" />
          <span>Resolution Logs ({historyItems.length})</span>
        </h2>

        {historyItems.length === 0 ? (
          <div className="text-xs text-muted-foreground italic p-4 border border-dashed rounded-lg bg-card/5">
            No resolved records found in local logs.
          </div>
        ) : (
          <div className="border border-border/30 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/40 border-b border-border/30">
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Tool / Task</th>
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Reviewer</th>
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Outcome</th>
                  <th className="text-left p-3 font-semibold text-xs text-muted-foreground">Notes</th>
                </tr>
              </thead>
              <tbody>
                {historyItems.map(item => (
                  <tr key={item.session_id} className="border-b border-border/20 last:border-0">
                    <td className="p-3 font-medium">
                      <div>{item.tool_name}</div>
                      <span className="text-[10px] text-muted-foreground font-mono">{item.session_id}</span>
                    </td>
                    <td className="p-3 text-xs">
                      <div className="flex items-center gap-1">
                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                        <span>{item.reviewer || "System"}</span>
                      </div>
                    </td>
                    <td className="p-3 text-xs">
                      <span className={`font-bold px-2 py-0.5 rounded ${
                        item.status === "approved" ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
                      }`}>
                        {item.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="p-3 text-xs text-muted-foreground">
                      {item.notes || <span className="italic">No comments left</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

