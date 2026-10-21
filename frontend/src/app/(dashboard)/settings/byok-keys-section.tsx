"use client";

import * as React from "react";
import { apiClient } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AnimatedCard } from "@/components/ui/animated-card";
import {
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Key,
  Plus,
  RefreshCw,
  Trash2,
  CheckCircle2,
  XCircle,
  Loader2,
  ShieldCheck,
} from "lucide-react";

export type ProviderId = "groq" | "gemini" | "openrouter" | "openai" | "anthropic";

export interface ProviderMeta {
  id: ProviderId;
  name: string;
  detail: string;
}

export const BYOK_PROVIDERS: ProviderMeta[] = [
  { id: "groq", name: "Groq", detail: "Ultra-fast inference (Llama 3.3 / Whisper)" },
  { id: "gemini", name: "Gemini", detail: "Google Gemini 2.0 Flash / Pro" },
  { id: "openrouter", name: "OpenRouter", detail: "DeepSeek R1 / multi-model swarm" },
  { id: "openai", name: "OpenAI", detail: "GPT-4o / GPT-4o-mini" },
  { id: "anthropic", name: "Anthropic", detail: "Claude 3.5 Sonnet / Haiku" },
];

export interface UserKeyRecord {
  provider: string;
  key_preview: string;
  is_valid: boolean;
  last_validated_at: string | null;
  last_error: string | null;
}

export function ByokKeysSection() {
  const [keys, setKeys] = React.useState<Record<string, UserKeyRecord>>({});
  const [loading, setLoading] = React.useState<boolean>(true);
  const [validatingProvider, setValidatingProvider] = React.useState<string | null>(null);
  const [deletingProvider, setDeletingProvider] = React.useState<string | null>(null);

  // Dialog state
  const [dialogOpen, setDialogOpen] = React.useState<boolean>(false);
  const [selectedProvider, setSelectedProvider] = React.useState<ProviderId>("groq");
  const [rawKeyInput, setRawKeyInput] = React.useState<string>("");
  const [savingKey, setSavingKey] = React.useState<boolean>(false);
  const [dialogError, setDialogError] = React.useState<string | null>(null);

  // Status message
  const [feedback, setFeedback] = React.useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchKeys = React.useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get<UserKeyRecord[]>("/api/v1/user-keys");
      const mapped: Record<string, UserKeyRecord> = {};
      if (Array.isArray(res.data)) {
        res.data.forEach((k) => {
          mapped[k.provider.toLowerCase()] = k;
        });
      }
      setKeys(mapped);
    } catch (err: unknown) {
      // Graceful fallback for initial load
      setKeys({});
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleOpenDialog = (providerId?: ProviderId) => {
    setSelectedProvider(providerId || "groq");
    setRawKeyInput("");
    setDialogError(null);
    setDialogOpen(true);
  };

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawKeyInput.trim()) {
      setDialogError("Please enter an API key.");
      return;
    }

    setSavingKey(true);
    setDialogError(null);

    try {
      await apiClient.post("/api/v1/user-keys", {
        provider: selectedProvider,
        api_key: rawKeyInput.trim(),
      });

      setDialogOpen(false);
      setRawKeyInput("");
      setFeedback({
        type: "success",
        text: `Key for ${BYOK_PROVIDERS.find((p) => p.id === selectedProvider)?.name || selectedProvider} verified and saved successfully.`,
      });
      await fetchKeys();
    } catch (err: any) {
      const errorMsg =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.data?.detail ||
        err?.data?.message ||
        err?.message ||
        "Failed to validate and save key.";
      setDialogError(errorMsg);
    } finally {
      setSavingKey(false);
    }
  };

  const handleValidateKey = async (providerId: string) => {
    setValidatingProvider(providerId);
    setFeedback(null);
    try {
      const res = await apiClient.post<{ is_valid: boolean; last_error?: string | null }>(
        `/api/v1/user-keys/${providerId}/validate`
      );
      if (res.data.is_valid) {
        setFeedback({
          type: "success",
          text: `Key for ${providerId.toUpperCase()} is valid and active.`,
        });
      } else {
        setFeedback({
          type: "error",
          text: `Validation failed: ${res.data.last_error || "Invalid key"}`,
        });
      }
      await fetchKeys();
    } catch (err: any) {
      setFeedback({
        type: "error",
        text: err?.response?.data?.detail || "Validation request failed.",
      });
    } finally {
      setValidatingProvider(null);
    }
  };

  const handleDeleteKey = async (providerId: string) => {
    const provName = BYOK_PROVIDERS.find((p) => p.id === providerId)?.name || providerId;
    const confirmed = window.confirm(
      `Are you sure you want to delete your custom API key for ${provName}? ASEP will fall back to platform env keys.`
    );
    if (!confirmed) return;

    setDeletingProvider(providerId);
    setFeedback(null);
    try {
      await apiClient.delete(`/api/v1/user-keys/${providerId}`);
      setFeedback({
        type: "success",
        text: `Custom key for ${provName} deleted. Platform fallback active.`,
      });
      await fetchKeys();
    } catch (err: any) {
      setFeedback({
        type: "error",
        text: err?.response?.data?.detail || "Failed to delete key.",
      });
    } finally {
      setDeletingProvider(null);
    }
  };

  return (
    <>
      <AnimatedCard className="border-border/40 bg-card/30 shadow-sm mb-6">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle className="text-xl font-bold flex items-center gap-2">
              <Key className="h-5 w-5 text-primary" /> Your API Keys (BYOK)
            </CardTitle>
            <CardDescription>
              Bring Your Own Key: your custom keys take precedence for your requests. If not set,
              the platform fallback key is used automatically. Encrypted at rest.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchKeys}
              disabled={loading}
              className="gap-1.5 text-xs"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={() => handleOpenDialog()}
              className="gap-1.5 text-xs font-semibold"
            >
              <Plus className="h-3.5 w-3.5" />
              Add Key
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {feedback && (
            <div
              className={`p-3 text-xs rounded-lg flex items-center justify-between border ${
                feedback.type === "success"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-400"
              }`}
            >
              <div className="flex items-center gap-2">
                {feedback.type === "success" ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 shrink-0" />
                )}
                <span>{feedback.text}</span>
              </div>
              <button
                onClick={() => setFeedback(null)}
                className="text-muted-foreground hover:text-foreground text-xs"
              >
                ✕
              </button>
            </div>
          )}

          {/* BYOK Providers Table */}
          <div className="overflow-x-auto rounded-xl border border-border/40 bg-background/40">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted/40 border-b border-border/40 text-xs text-muted-foreground uppercase font-medium">
                <tr>
                  <th className="py-3 px-4">Provider</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Key Preview</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/20">
                {BYOK_PROVIDERS.map((prov) => {
                  const keyData = keys[prov.id];
                  const hasKey = Boolean(keyData);
                  const isValid = keyData?.is_valid ?? false;

                  return (
                    <tr key={prov.id} className="hover:bg-muted/10 transition-colors">
                      <td className="py-3.5 px-4">
                        <div>
                          <p className="font-semibold text-foreground">{prov.name}</p>
                          <p className="text-xs text-muted-foreground">{prov.detail}</p>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        {hasKey ? (
                          isValid ? (
                            <Badge className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 text-xs font-semibold">
                              Active
                            </Badge>
                          ) : (
                            <Badge
                              className="bg-rose-500/15 text-rose-400 border-rose-500/30 text-xs font-semibold"
                              title={keyData.last_error || "Validation check failed"}
                            >
                              Invalid
                            </Badge>
                          )
                        ) : (
                          <Badge
                            variant="outline"
                            className="text-muted-foreground border-border/40 text-xs"
                          >
                            Not set
                          </Badge>
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-xs text-muted-foreground">
                        {hasKey ? keyData.key_preview : "—"}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {hasKey ? (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleOpenDialog(prov.id)}
                                className="h-7 px-2.5 text-xs"
                              >
                                Update
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleValidateKey(prov.id)}
                                disabled={validatingProvider === prov.id}
                                className="h-7 px-2.5 text-xs gap-1"
                              >
                                {validatingProvider === prov.id ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <ShieldCheck className="h-3 w-3" />
                                )}
                                Validate
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDeleteKey(prov.id)}
                                disabled={deletingProvider === prov.id}
                                className="h-7 px-2 text-xs"
                              >
                                {deletingProvider === prov.id ? (
                                  <Loader2 className="h-3 w-3 animate-spin" />
                                ) : (
                                  <Trash2 className="h-3 w-3" />
                                )}
                              </Button>
                            </>
                          ) : (
                            <Button
                              size="sm"
                              onClick={() => handleOpenDialog(prov.id)}
                              className="h-7 px-2.5 text-xs gap-1"
                            >
                              <Plus className="h-3 w-3" />
                              Add
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </AnimatedCard>

      {/* Add / Update Key Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="h-4 w-4 text-primary" />
              {keys[selectedProvider] ? "Update API Key" : "Add Your API Key"}
            </DialogTitle>
            <DialogDescription>
              Enter your credentials for this provider. We will validate the key immediately against
              the provider's verification endpoint before storing it encrypted at rest.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSaveKey} className="space-y-4 py-2">
            {dialogError && (
              <div className="p-3 text-xs bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 flex items-center gap-2">
                <XCircle className="h-4 w-4 shrink-0" />
                <span>{dialogError}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase">
                Provider
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value as ProviderId)}
                className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              >
                {BYOK_PROVIDERS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} — {p.detail}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-muted-foreground uppercase">
                API Key
              </label>
              <Input
                type="password"
                value={rawKeyInput}
                onChange={(e) => setRawKeyInput(e.target.value)}
                placeholder="Enter secret key (e.g. gsk_..., sk-...)"
                autoComplete="new-password"
                required
                className="h-9 font-mono text-sm"
              />
            </div>

            <DialogFooter className="pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setDialogOpen(false)}
                disabled={savingKey}
              >
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={savingKey} className="gap-1.5 font-semibold">
                {savingKey && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                {savingKey ? "Validating & Saving..." : "Save Key"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
