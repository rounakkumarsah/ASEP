"use client";

import * as React from "react";
import { useAuth } from "@/lib/providers/auth-provider";
import { apiClient } from "@/lib/api/client";
import { 
  User as UserIcon, 
  Building2, 
  Sparkles, 
  Check,
  Lock,
  Key,
  Settings2,
  Bell,
  Paintbrush,
  CreditCard,
  UserCheck
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = React.useState<
    "profile" | "account" | "security" | "api_keys" | "preferences" | "notifications" | "theme" | "org" | "billing" | "llm"
  >("profile");

  // Profile Form state
  const [firstName, setFirstName] = React.useState(user?.first_name || "");
  const [lastName, setLastName] = React.useState(user?.last_name || "");
  const [profileSaving, setProfileSaving] = React.useState(false);
  const [profileSuccess, setProfileSuccess] = React.useState(false);

  // Org Form State
  const [orgName, setOrgName] = React.useState("");
  const [orgLoading, setOrgLoading] = React.useState(true);
  const [orgSaving, setOrgSaving] = React.useState(false);

  React.useEffect(() => {
    if (user) {
      setFirstName(user.first_name || "");
      setLastName(user.last_name || "");
    }
  }, [user]);

  React.useEffect(() => {
    apiClient.get("/api/v1/organizations/me")
      .then(res => {
        if (res.data?.name) setOrgName(res.data.name);
      })
      .catch(() => {})
      .finally(() => setOrgLoading(false));
  }, []);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaving(true);
    try {
      await apiClient.patch("/api/v1/auth/me", {
        first_name: firstName,
        last_name: lastName,
      });
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch {
      alert("Failed to update profile");
    } finally {
      setProfileSaving(false);
    }
  };

  const handleOrgSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setOrgSaving(true);
    try {
      if (orgName) {
        await apiClient.patch("/api/v1/organizations/me", { name: orgName });
        alert("Organization settings updated successfully.");
      }
    } catch {
      try {
        await apiClient.post("/api/v1/organizations", { name: orgName });
        alert("Organization created successfully.");
      } catch (err: unknown) {
        const message = err && typeof err === "object" && "response" in err 
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail 
          : "Failed to save organization";
        alert(message);
      }
    } finally {
      setOrgSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure profile details, multi-tenant workspace credentials, theme preferences, and billing.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Left tabs selector */}
        <div className="lg:w-64 flex flex-col gap-1 shrink-0">
          {[
            { id: "profile", label: "User Profile", icon: <UserIcon className="h-4 w-4" /> },
            { id: "account", label: "Account Details", icon: <UserCheck className="h-4 w-4" /> },
            { id: "security", label: "Security & Passwords", icon: <Lock className="h-4 w-4" /> },
            { id: "api_keys", label: "API Keys", icon: <Key className="h-4 w-4" /> },
            { id: "preferences", label: "Preferences", icon: <Settings2 className="h-4 w-4" /> },
            { id: "notifications", label: "Notifications", icon: <Bell className="h-4 w-4" /> },
            { id: "theme", label: "Theme Preferences", icon: <Paintbrush className="h-4 w-4" /> },
            { id: "org", label: "Organization & Workspace", icon: <Building2 className="h-4 w-4" /> },
            { id: "billing", label: "Billing & Subscriptions", icon: <CreditCard className="h-4 w-4" /> },
            { id: "llm", label: "LLM Providers", icon: <Sparkles className="h-4 w-4" /> },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex items-center gap-2.5 px-4 py-2.5 rounded-lg text-sm text-left transition-all outline-none ${
                activeTab === tab.id
                  ? "bg-primary/10 text-primary font-semibold border-l-2 border-primary rounded-l-none"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Right workspace panels */}
        <div className="flex-1 max-w-3xl space-y-6">
          {activeTab === "profile" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Profile Details</CardTitle>
                <CardDescription>Update your account details and profile information.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <form onSubmit={handleProfileSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground uppercase">First Name</label>
                      <Input value={firstName} onChange={e => setFirstName(e.target.value)} />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground uppercase">Last Name</label>
                      <Input value={lastName} onChange={e => setLastName(e.target.value)} />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Username</label>
                    <Input value={user?.username || ""} disabled />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Email Address</label>
                    <Input value={user?.email || ""} disabled />
                  </div>
                  <div className="flex items-center gap-4 pt-2">
                    <Button type="submit" disabled={profileSaving}>
                      {profileSaving ? "Saving..." : "Save Changes"}
                    </Button>
                    {profileSuccess && (
                      <span className="text-sm text-green-500 font-medium flex items-center gap-1">
                        <Check className="h-4 w-4" /> Updated
                      </span>
                    )}
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {activeTab === "account" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Account Details</CardTitle>
                <CardDescription>View your core account registration parameters.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="font-semibold text-muted-foreground text-xs uppercase block">User ID</span>
                    <span className="font-mono text-xs">{user?.id}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-muted-foreground text-xs uppercase block">Role Privilege</span>
                    <span>{user?.role === "admin" ? "Administrator" : "Standard User"}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-muted-foreground text-xs uppercase block">Account Verified</span>
                    <span>{user?.email_verified ? "Yes" : "No"}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-muted-foreground text-xs uppercase block">Status</span>
                    <Badge variant="default">Active</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "security" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Security & Credentials</CardTitle>
                <CardDescription>Configure credential safety policies and passwords.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="p-3 border rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Cloudflare Turnstile</p>
                      <p className="text-xs text-muted-foreground">Applies anti-bot validation checkpoints during entry gates.</p>
                    </div>
                    <Badge variant="default">Active</Badge>
                  </div>
                  <div className="p-3 border rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">OAuth Integrations</p>
                      <p className="text-xs text-muted-foreground">Passwordless Single Sign-On configuration.</p>
                    </div>
                    <Badge variant="default">Linked</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "api_keys" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Developer API Keys</CardTitle>
                <CardDescription>Scoped authorization key credentials for integration pipelines.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-muted-foreground">
                <p>API Keys are managed inside specific projects to preserve strict multi-tenant boundary boundaries.</p>
                <Button onClick={() => window.location.href = "/api-keys"} variant="outline" className="font-semibold">
                  Manage API Keys
                </Button>
              </CardContent>
            </Card>
          )}

          {activeTab === "preferences" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Preferences</CardTitle>
                <CardDescription>Configure localized parameter defaults.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Default Language</label>
                  <select className="text-sm p-2 rounded border bg-background w-full">
                    <option value="en">English (United States)</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "notifications" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Notifications</CardTitle>
                <CardDescription>Control telemetry alerting channels.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Security & Audit Alerts</p>
                      <p className="text-xs text-muted-foreground">Receive critical notifications when permissions are requested.</p>
                    </div>
                    <Badge variant="default">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Weekly Evaluation Reports</p>
                      <p className="text-xs text-muted-foreground">Diagnostic summaries of benchmark runs.</p>
                    </div>
                    <Badge variant="secondary">Disabled</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "theme" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Theme Preferences</CardTitle>
                <CardDescription>Toggle between dark and light appearance modes.</CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between p-6">
                <div>
                  <p className="font-semibold text-sm">Appearance Mode</p>
                  <p className="text-xs text-muted-foreground">Adjust display color palettes for optimal visual comfort.</p>
                </div>
                <ThemeToggle />
              </CardContent>
            </Card>
          )}

          {activeTab === "org" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Organization & Workspace</CardTitle>
                <CardDescription>Configure workspace settings and organizational boundaries.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {orgLoading ? (
                  <p className="text-sm text-muted-foreground">Loading workspace details...</p>
                ) : (
                  <form onSubmit={handleOrgSubmit} className="space-y-4">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-muted-foreground uppercase">Organization Name</label>
                      <Input
                        value={orgName}
                        onChange={e => setOrgName(e.target.value)}
                        placeholder="e.g. Acme Software Inc."
                        required
                      />
                    </div>
                    <Button type="submit" disabled={orgSaving}>
                      {orgSaving ? "Saving..." : "Save Organization"}
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          )}

          {activeTab === "billing" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Billing & Subscriptions</CardTitle>
                <CardDescription>Manage workspace subscription tiers and payment settings.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-muted-foreground">
                <p>Subscriptions are managed securely via Razorpay checkout integration.</p>
                <Button onClick={() => window.location.href = "/billing"} className="font-semibold gap-2">
                  <CreditCard className="h-4 w-4" />
                  View Billing Panel
                </Button>
              </CardContent>
            </Card>
          )}

          {activeTab === "llm" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">LLM Provider Status</CardTitle>
                <CardDescription>View connected AI models and runtime endpoints.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Ollama Local LLM</p>
                      <p className="text-xs text-muted-foreground">Model: qwen2.5-coder:7b</p>
                    </div>
                    <Badge variant="default">Active</Badge>
                  </div>
                  <div className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Embedding Engine</p>
                      <p className="text-xs text-muted-foreground">Model: nomic-embed-text (1536 dim)</p>
                    </div>
                    <Badge variant="default">Active</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
