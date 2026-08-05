"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
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
  UserCheck,
  Shield,
  Users,
  KeyRound,
  Laptop,
  AlertTriangle,
  Plug
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ui/theme-toggle";

type SettingsTab = 
  | "profile"
  | "account"
  | "security"
  | "password"
  | "mfa"
  | "notifications"
  | "preferences"
  | "appearance"
  | "api_keys"
  | "billing"
  | "org"
  | "team"
  | "llm"
  | "integrations"
  | "sessions"
  | "delete_account";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as SettingsTab) || "profile";
  const [activeTab, setActiveTab] = React.useState<SettingsTab>(initialTab);

  // Sync tab with URL parameter if present
  React.useEffect(() => {
    const tabParam = searchParams.get("tab") as SettingsTab;
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  // Profile Form state
  const [firstName, setFirstName] = React.useState(user?.first_name || "");
  const [lastName, setLastName] = React.useState(user?.last_name || "");
  const [profileSaving, setProfileSaving] = React.useState(false);
  const [profileSuccess, setProfileSuccess] = React.useState(false);

  // Password Change Form state
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [passwordSaving, setPasswordSaving] = React.useState(false);
  const [passwordMessage, setPasswordMessage] = React.useState<{ text: string; error: boolean } | null>(null);

  // Org Form State
  const [orgName, setOrgName] = React.useState("");
  const [orgLoading, setOrgLoading] = React.useState(true);
  const [orgSaving, setOrgSaving] = React.useState(false);

  // Team members state
  const [teamMembers, setTeamMembers] = React.useState<Array<{ id: string; email: string; role: string; first_name?: string }>>([]);
  const [teamLoading, setTeamLoading] = React.useState(false);

  // Active Sessions state
  const [sessions, setSessions] = React.useState<Array<{ id: string; ip_address: string; user_agent: string; current: boolean; last_active: string }>>([]);
  const [sessionsLoading, setSessionsLoading] = React.useState(false);

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

  React.useEffect(() => {
    if (activeTab === "team") {
      setTeamLoading(true);
      apiClient.get("/api/v1/organizations/members")
        .then(res => setTeamMembers(res.data || []))
        .catch(() => {})
        .finally(() => setTeamLoading(false));
    }
    if (activeTab === "sessions") {
      setSessionsLoading(true);
      apiClient.get("/api/v1/auth/sessions")
        .then(res => setSessions(res.data || []))
        .catch(() => {})
        .finally(() => setSessionsLoading(false));
    }
  }, [activeTab]);

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

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPasswordMessage({ text: "New passwords do not match.", error: true });
      return;
    }
    setPasswordSaving(true);
    setPasswordMessage(null);
    try {
      await apiClient.post("/api/v1/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMessage({ text: "Password updated successfully.", error: false });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      const message = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to update password";
      setPasswordMessage({ text: message || "Failed to update password", error: true });
    } finally {
      setPasswordSaving(false);
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

  const tabsList: Array<{ id: SettingsTab; label: string; icon: React.ReactNode }> = [
    { id: "profile", label: "Profile", icon: <UserIcon className="h-4 w-4" /> },
    { id: "account", label: "Account", icon: <UserCheck className="h-4 w-4" /> },
    { id: "security", label: "Security", icon: <Lock className="h-4 w-4" /> },
    { id: "password", label: "Password", icon: <KeyRound className="h-4 w-4" /> },
    { id: "mfa", label: "MFA", icon: <Shield className="h-4 w-4" /> },
    { id: "notifications", label: "Notifications", icon: <Bell className="h-4 w-4" /> },
    { id: "preferences", label: "Preferences", icon: <Settings2 className="h-4 w-4" /> },
    { id: "appearance", label: "Appearance", icon: <Paintbrush className="h-4 w-4" /> },
    { id: "api_keys", label: "API Keys", icon: <Key className="h-4 w-4" /> },
    { id: "billing", label: "Billing", icon: <CreditCard className="h-4 w-4" /> },
    { id: "org", label: "Organization", icon: <Building2 className="h-4 w-4" /> },
    { id: "team", label: "Team", icon: <Users className="h-4 w-4" /> },
    { id: "llm", label: "LLM Providers", icon: <Sparkles className="h-4 w-4" /> },
    { id: "integrations", label: "Integrations", icon: <Plug className="h-4 w-4" /> },
    { id: "sessions", label: "Sessions", icon: <Laptop className="h-4 w-4" /> },
    { id: "delete_account", label: "Delete Account", icon: <AlertTriangle className="h-4 w-4" /> },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
        <p className="text-muted-foreground mt-1">
          Configure profile details, multi-tenant workspace credentials, theme preferences, and security settings.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Left tabs selector */}
        <div className="lg:w-64 flex flex-col gap-1 shrink-0">
          {tabsList.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
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
                <CardDescription>Configure credential safety policies and authentication safeguards.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Cloudflare Turnstile</p>
                      <p className="text-xs text-muted-foreground">Applies anti-bot validation checkpoints during entry gates.</p>
                    </div>
                    <Badge variant="default">Active</Badge>
                  </div>
                  <div className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">JWT Authentication</p>
                      <p className="text-xs text-muted-foreground">HTTP-only SameSite cookie security policy.</p>
                    </div>
                    <Badge variant="default">Strict</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "password" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Password Management</CardTitle>
                <CardDescription>Update your account login password.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Current Password</label>
                    <Input 
                      type="password"
                      value={currentPassword}
                      onChange={e => setCurrentPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">New Password</label>
                    <Input 
                      type="password"
                      value={newPassword}
                      onChange={e => setNewPassword(e.target.value)}
                      required
                      minLength={8}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Confirm New Password</label>
                    <Input 
                      type="password"
                      value={confirmPassword}
                      onChange={e => setConfirmPassword(e.target.value)}
                      required
                      minLength={8}
                    />
                  </div>
                  {passwordMessage && (
                    <div className={`text-sm ${passwordMessage.error ? "text-destructive" : "text-green-500"}`}>
                      {passwordMessage.text}
                    </div>
                  )}
                  <Button type="submit" disabled={passwordSaving}>
                    {passwordSaving ? "Updating Password..." : "Update Password"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {activeTab === "mfa" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Multi-Factor Authentication (MFA)</CardTitle>
                <CardDescription>Add an extra layer of security to your account.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 border border-border/50 rounded-lg flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-sm">Authenticator App (TOTP)</p>
                    <p className="text-xs text-muted-foreground">Use Google Authenticator or 1Password to generate verification codes.</p>
                  </div>
                  <Badge variant="outline">Not Configured</Badge>
                </div>
                <Button variant="outline" size="sm">Enable MFA</Button>
              </CardContent>
            </Card>
          )}

          {activeTab === "notifications" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Notifications</CardTitle>
                <CardDescription>Control telemetry alerting channels and system notifications.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border border-border/50 rounded-lg">
                    <div>
                      <p className="font-semibold text-sm">Security & Audit Alerts</p>
                      <p className="text-xs text-muted-foreground">Receive critical notifications when permissions are requested.</p>
                    </div>
                    <Badge variant="default">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border border-border/50 rounded-lg">
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

          {activeTab === "preferences" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Preferences</CardTitle>
                <CardDescription>Configure localized parameter defaults and runtime settings.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Default Language</label>
                  <select className="text-sm p-2 rounded border bg-background w-full">
                    <option value="en">English (United States)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Preferred AI Provider</label>
                  <select className="text-sm p-2 rounded border bg-background w-full">
                    <option value="ollama">Local Ollama (qwen2.5-coder:7b)</option>
                    <option value="gemini">Google Gemini 1.5 Pro</option>
                    <option value="openai">OpenAI GPT-4o</option>
                  </select>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "appearance" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Appearance</CardTitle>
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

          {activeTab === "team" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Team Members</CardTitle>
                <CardDescription>Manage user roles and team access within your organization.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {teamLoading ? (
                  <p className="text-sm text-muted-foreground">Loading team members...</p>
                ) : teamMembers.length === 0 ? (
                  <div className="text-center py-6 text-muted-foreground">
                    <p className="text-sm">No team members found.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {teamMembers.map(member => (
                      <div key={member.id} className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-sm">{member.first_name || member.email}</p>
                          <p className="text-xs text-muted-foreground">{member.email}</p>
                        </div>
                        <Badge variant="outline">{member.role || "member"}</Badge>
                      </div>
                    ))}
                  </div>
                )}
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

          {activeTab === "integrations" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Connected Integrations</CardTitle>
                <CardDescription>Integrations with third-party developer platforms.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Cloudflare Turnstile</p>
                      <p className="text-xs text-muted-foreground">Anti-bot security verification.</p>
                    </div>
                    <Badge variant="default">Connected</Badge>
                  </div>
                  <div className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-sm">Razorpay Subscriptions</p>
                      <p className="text-xs text-muted-foreground">Payment processing & subscriptions.</p>
                    </div>
                    <Badge variant="default">Connected</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "sessions" && (
            <Card className="border-border/40 bg-card/30">
              <CardHeader>
                <CardTitle className="text-lg font-bold">Active Sessions</CardTitle>
                <CardDescription>Manage active logins across browsers and devices.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {sessionsLoading ? (
                  <p className="text-sm text-muted-foreground">Loading active sessions...</p>
                ) : sessions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No active sessions found.</p>
                ) : (
                  <div className="space-y-3">
                    {sessions.map(s => (
                      <div key={s.id} className="p-3 border border-border/50 rounded-lg flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-sm">{s.user_agent}</p>
                          <p className="text-xs text-muted-foreground">IP: {s.ip_address} • {s.last_active}</p>
                        </div>
                        {s.current ? <Badge variant="default">Current Session</Badge> : <Badge variant="outline">Active</Badge>}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {activeTab === "delete_account" && (
            <Card className="border-destructive/40 bg-destructive/5">
              <CardHeader>
                <CardTitle className="text-lg font-bold text-destructive">Danger Zone — Delete Account</CardTitle>
                <CardDescription>Permanently delete your account and all associated workspace data.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Once deleted, your account cannot be recovered. All projects, API keys, and workspace settings will be permanently removed.
                </p>
                <Button 
                  variant="destructive"
                  onClick={() => {
                    if (confirm("Are you ABSOLUTELY sure you want to delete your account? This action cannot be undone.")) {
                      apiClient.delete("/api/v1/auth/me")
                        .then(() => logout())
                        .catch(() => alert("Failed to delete account."));
                    }
                  }}
                >
                  Delete Account
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
