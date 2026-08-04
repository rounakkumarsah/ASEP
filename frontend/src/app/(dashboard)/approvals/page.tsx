"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { useAuth } from "@/lib/providers/auth-provider";
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Loader2, 
  AlertTriangle,
  ShieldCheck,
  User,
  Sparkles
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
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

export default function ApprovalsPage() {
  const { user } = useAuth();
  const [queue, setQueue] = React.useState<ReviewSession[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [notes, setNotes] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState<string | null>(null);

  const fetchQueue = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiClient.get("/api/v1/governance/hitl/queue");
      setQueue(res.data || []);
    } catch (err: unknown) {
      setError((err as Error).message || "Failed to load approval queue.");
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchQueue();
  }, []);

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

      {/* Pending Queue Section */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          <span>Pending Approvals ({pendingItems.length})</span>
        </h2>

        {pendingItems.length === 0 ? (
          <Card className="border border-dashed p-10 text-center flex flex-col items-center justify-center text-muted-foreground">
            <ShieldCheck className="h-10 w-10 text-emerald-500 mb-2" />
            <CardTitle className="text-base font-bold text-foreground">No pending approvals</CardTitle>
            <CardDescription className="max-w-xs mt-1">
              No tasks currently require human authorization. All agents running automatically.
            </CardDescription>
          </Card>
        ) : (
          <div className="space-y-4">
            {pendingItems.map(item => (
              <Card key={item.session_id} className="border-border/40 bg-card/30">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono bg-muted px-2 py-0.5 rounded text-muted-foreground">
                      Session: {item.session_id}
                    </span>
                    <span className="text-xs font-bold text-yellow-500 bg-yellow-500/10 px-2 py-0.5 rounded-full uppercase animate-pulse">
                      Pending Approval
                    </span>
                  </div>
                  <CardTitle className="text-lg font-bold pt-2 flex items-center gap-2 text-foreground">
                    <Sparkles className="h-4 w-4 text-primary" />
                    <span>Run Command: {item.tool_name}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Arguments inspector */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Target Arguments</label>
                    <pre className="p-3 bg-muted/60 border border-border/30 rounded-lg text-xs font-mono overflow-x-auto text-foreground">
                      {JSON.stringify(item.args, null, 2)}
                    </pre>
                  </div>

                  {/* Decision fields */}
                  <div className="space-y-3 pt-2">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground uppercase">Reviewer Comments</label>
                      <Input
                        value={notes[item.session_id] || ""}
                        onChange={e => handleNoteChange(item.session_id, e.target.value)}
                        placeholder="Add review notes or instructions for the agent..."
                      />
                    </div>

                    <div className="flex gap-2 justify-end">
                      <Button
                        variant="outline"
                        onClick={() => handleDecision(item.session_id, "reject")}
                        disabled={submitting === item.session_id}
                        className="border-red-500/30 hover:bg-red-500/10 text-red-500 gap-1.5 font-semibold"
                      >
                        <XCircle className="h-4 w-4" />
                        <span>Reject</span>
                      </Button>
                      <Button
                        onClick={() => handleDecision(item.session_id, "approve")}
                        disabled={submitting === item.session_id}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5 font-semibold"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Authorize</span>
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* History Queue Section */}
      <div className="space-y-4 pt-4">
        <h2 className="text-xl font-bold flex items-center gap-2 text-muted-foreground">
          <ShieldCheck className="h-5 w-5" />
          <span>Resolution Logs ({historyItems.length})</span>
        </h2>

        {historyItems.length > 0 && (
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
