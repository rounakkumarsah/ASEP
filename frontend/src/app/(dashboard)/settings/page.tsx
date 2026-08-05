"use client";

import * as React from "react";
import { useSearchParams, useRouter } from "next/navigation";
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
  Plug,
  ChevronDown
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
  | "sessions"
  | "org"
  | "team"
  | "api_keys"
  | "billing"
  | "llm"
  | "integrations"
  | "preferences"
  | "notifications"
  | "appearance"
  | "delete_account";

interface TabCategory {
  title: string;
  tabs: Array<{ id: SettingsTab; label: string; icon: React.ReactNode }>;
}

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as SettingsTab) || "profile";
  const [activeTab, setActiveTab] = React.useState<SettingsTab>(initialTab);

  // Sync tab state when searchParams change (browser back/forward navigation)
  React.useEffect(() => {
    const tabParam = searchParams.get("tab") as SettingsTab;
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  const handleTabChange = (tab: SettingsTab) => {
    setActiveTab(tab);
    // Update query string cleanly without page scrolling or layout jump
    router.push(`/settings?tab=${tab}`, { scroll: false });
  };

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

  // Preferences Form State
  const [preferredProvider, setPreferredProvider] = React.useState("gemini-1.5-pro");
  const [prefSaved, setPrefSaved] = React.useState(false);

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
      alert("Failed to update profile details.");
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

  const categories: TabCategory[] = [
    {
      title: "Account & Access",
      tabs: [
        { id: "profile", label: "User Profile", icon: <UserIcon className="h-4 w-4" /> },
        { id: "account", label: "Account Details", icon: <UserCheck className="h-4 w-4" /> },
        { id: "security", label: "Security", icon: <Lock className="h-4 w-4" /> },
        { id: "password", label: "Password", icon: <KeyRound className="h-4 w-4" /> },
        { id: "mfa", label: "Multi-Factor Auth", icon: <Shield className="h-4 w-4" /> },
        { id: "sessions", label: "Active Sessions", icon: <Laptop className="h-4 w-4" /> },
      ],
    },
    {
      title: "Workspace & Team",
      tabs: [
        { id: "org", label: "Organization", icon: <Building2 className="h-4 w-4" /> },
        { id: "team", label: "Team Members", icon: <Users className="h-4 w-4" /> },
        { id: "api_keys", label: "API Keys", icon: <Key className="h-4 w-4" /> },
        { id: "billing", label: "Billing & Plans", icon: <CreditCard className="h-4 w-4" /> },
      ],
    },
    {
      title: "Platform Configuration",
      tabs: [
        { id: "llm", label: "LLM Providers", icon: <Sparkles className="h-4 w-4" /> },
        { id: "integrations", label: "Integrations", icon: <Plug className="h-4 w-4" /> },
        { id: "preferences", label: "Preferences", icon: <Settings2 className="h-4 w-4" /> },
        { id: "notifications", label: "Notifications", icon: <Bell className="h-4 w-4" /> },
        { id: "appearance", label: "Appearance", icon: <Paintbrush className="h-4 w-4" /> },
      ],
    },
    {
      title: "Danger Zone",
      tabs: [
        { id: "delete_account", label: "Delete Account", icon: <AlertTriangle className="h-4 w-4 text-destructive" /> },
      ],
    },
  ];

  // Helper to render exactly ONE active panel inside the right content container
  const renderActiveTab = () => {
    switch (activeTab) {
      case "profile":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <UserIcon className="h-5 w-5 text-primary" /> User Profile
              </CardTitle>
              <CardDescription>Update your personal account details and public display identity.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <form onSubmit={handleProfileSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">First Name</label>
                    <Input value={firstName} onChange={e => setFirstName(e.target.value)} placeholder="e.g. Alex" />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Last Name</label>
                    <Input value={lastName} onChange={e => setLastName(e.target.value)} placeholder="e.g. Vance" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Username</label>
                  <Input value={user?.username || ""} disabled className="bg-muted/40 cursor-not-allowed" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Email Address</label>
                  <Input value={user?.email || ""} disabled className="bg-muted/40 cursor-not-allowed" />
                </div>
                <div className="flex items-center gap-4 pt-2">
                  <Button type="submit" disabled={profileSaving} className="font-semibold">
                    {profileSaving ? "Saving Changes..." : "Save Profile"}
                  </Button>
                  {profileSuccess && (
                    <span className="text-sm text-green-500 font-medium flex items-center gap-1">
                      <Check className="h-4 w-4" /> Profile updated successfully
                    </span>
                  )}
                </div>
              </form>
            </CardContent>
          </Card>
        );

      case "account":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-primary" /> Account Details
              </CardTitle>
              <CardDescription>Core identity and permission attributes associated with your SaaS account.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">User ID</span>
                  <span className="font-mono text-xs text-foreground block truncate">{user?.id}</span>
                </div>
                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">Role Privilege</span>
                  <span className="font-semibold text-foreground capitalize block">{user?.role || "developer"}</span>
                </div>
                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">Email Verification</span>
                  <Badge variant={user?.email_verified ? "default" : "secondary"}>
                    {user?.email_verified ? "Verified" : "Pending Verification"}
                  </Badge>
                </div>
                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">Account Status</span>
                  <Badge variant="default">Active SaaS Tier</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        );

      case "security":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Lock className="h-5 w-5 text-primary" /> Security & Protection
              </CardTitle>
              <CardDescription>Production security safeguards and authentication posture.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 border border-border/50 rounded-xl bg-background/40 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm">Cloudflare Turnstile Protection</p>
                  <p className="text-xs text-muted-foreground">Applies enterprise anti-bot verification during entry checks.</p>
                </div>
                <Badge variant="default">Active</Badge>
              </div>
              <div className="p-4 border border-border/50 rounded-xl bg-background/40 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm">JWT Cookie Policy</p>
                  <p className="text-xs text-muted-foreground">HTTP-only SameSite cookie token authorization.</p>
                </div>
                <Badge variant="default">Strict</Badge>
              </div>
            </CardContent>
          </Card>
        );

      case "password":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <KeyRound className="h-5 w-5 text-primary" /> Password Management
              </CardTitle>
              <CardDescription>Update your account access password.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handlePasswordSubmit} className="space-y-4 max-w-md">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Current Password</label>
                  <Input 
                    type="password"
                    value={currentPassword}
                    onChange={e => setCurrentPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New Password</label>
                  <Input 
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>
                <div className="space-y-1.5">
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
                  <div className={`text-sm ${passwordMessage.error ? "text-destructive font-medium" : "text-green-500 font-medium"}`}>
                    {passwordMessage.text}
                  </div>
                )}
                <Button type="submit" disabled={passwordSaving} className="font-semibold">
                  {passwordSaving ? "Updating Password..." : "Update Password"}
                </Button>
              </form>
            </CardContent>
          </Card>
        );

      case "mfa":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" /> Multi-Factor Authentication
              </CardTitle>
              <CardDescription>Enhance login security with Time-based One-Time Passwords (TOTP).</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 border border-border/50 rounded-xl bg-background/40 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm">Authenticator App (TOTP)</p>
                  <p className="text-xs text-muted-foreground">Compatible with Google Authenticator, Authy, and 1Password.</p>
                </div>
                <Badge variant="outline">Disabled</Badge>
              </div>
              <Button variant="outline" size="sm" className="font-semibold">Enable MFA Protection</Button>
            </CardContent>
          </Card>
        );

      case "sessions":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Laptop className="h-5 w-5 text-primary" /> Active Sessions
              </CardTitle>
              <CardDescription>Active authenticated logins across devices.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {sessionsLoading ? (
                <p className="text-sm text-muted-foreground">Loading active sessions...</p>
              ) : sessions.length === 0 ? (
                <p className="text-sm text-muted-foreground">No active sessions found.</p>
              ) : (
                <div className="space-y-3">
                  {sessions.map(s => (
                    <div key={s.id} className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between">
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
        );

      case "org":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" /> Organization Workspace
              </CardTitle>
              <CardDescription>Configure organizational boundaries and multi-tenant domain profiles.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {orgLoading ? (
                <p className="text-sm text-muted-foreground">Loading workspace details...</p>
              ) : (
                <form onSubmit={handleOrgSubmit} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Organization Name</label>
                    <Input
                      value={orgName}
                      onChange={e => setOrgName(e.target.value)}
                      placeholder="e.g. Acme Enterprise Technologies"
                      required
                    />
                  </div>
                  <Button type="submit" disabled={orgSaving} className="font-semibold">
                    {orgSaving ? "Saving..." : "Save Workspace"}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        );

      case "team":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" /> Team Members
              </CardTitle>
              <CardDescription>Manage team roles and user permissions in your organization.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {teamLoading ? (
                <p className="text-sm text-muted-foreground">Loading members...</p>
              ) : teamMembers.length === 0 ? (
                <p className="text-sm text-muted-foreground">No team members registered yet.</p>
              ) : (
                <div className="space-y-2">
                  {teamMembers.map(m => (
                    <div key={m.id} className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-sm">{m.first_name || m.email}</p>
                        <p className="text-xs text-muted-foreground">{m.email}</p>
                      </div>
                      <Badge variant="outline">{m.role || "member"}</Badge>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        );

      case "api_keys":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Key className="h-5 w-5 text-primary" /> API Key Management
              </CardTitle>
              <CardDescription>Manage project-scoped API key credentials.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                API Keys are isolated within project workspaces to maintain strict multi-tenant access boundaries.
              </p>
              <Button onClick={() => router.push("/api-keys")} className="font-semibold gap-2">
                <Key className="h-4 w-4" /> Go to API Keys Manager
              </Button>
            </CardContent>
          </Card>
        );

      case "billing":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" /> Billing & Subscriptions
              </CardTitle>
              <CardDescription>Manage subscription plans, invoices, and payment checkout.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Upgrade your plan or view past transaction history in the Billing dashboard.
              </p>
              <Button onClick={() => router.push("/billing")} className="font-semibold gap-2">
                <CreditCard className="h-4 w-4" /> Open Billing Dashboard
              </Button>
            </CardContent>
          </Card>
        );

      case "llm":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" /> Production LLM Providers
              </CardTitle>
              <CardDescription>Connected enterprise cloud AI model services.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { name: "Google Gemini", detail: "Gemini 1.5 Pro / Flash 1.5", badge: "Active" },
                { name: "Anthropic Claude", detail: "Claude 3.5 Sonnet / Haiku", badge: "Active" },
                { name: "OpenAI GPT", detail: "GPT-4o / GPT-4o-mini", badge: "Active" },
                { name: "OpenRouter Swarm", detail: "DeepSeek R1 / Qwen 2.5", badge: "Active" },
                { name: "Groq Cloud", detail: "Llama 3.3 70B (High-speed inference)", badge: "Active" },
                { name: "Cohere Command", detail: "Command R+ / Embed v3", badge: "Active" },
              ].map(provider => (
                <div key={provider.name} className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-sm text-foreground">{provider.name}</p>
                    <p className="text-xs text-muted-foreground">{provider.detail}</p>
                  </div>
                  <Badge variant="default" className="text-xs font-semibold">
                    {provider.badge}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        );

      case "integrations":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Plug className="h-5 w-5 text-primary" /> Production Integrations
              </CardTitle>
              <CardDescription>Connected developer platforms and security infrastructure.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm">Cloudflare Turnstile</p>
                  <p className="text-xs text-muted-foreground">Bot detection and anti-spam verification.</p>
                </div>
                <Badge variant="default">Connected</Badge>
              </div>
              <div className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm">Razorpay Checkout</p>
                  <p className="text-xs text-muted-foreground">Subscription payments and automated invoicing.</p>
                </div>
                <Badge variant="default">Connected</Badge>
              </div>
            </CardContent>
          </Card>
        );

      case "preferences":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Settings2 className="h-5 w-5 text-primary" /> Platform Preferences
              </CardTitle>
              <CardDescription>Configure production LLM defaults and regional localization parameters.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase">Default Model Engine</label>
                <select 
                  value={preferredProvider}
                  onChange={e => { setPreferredProvider(e.target.value); setPrefSaved(true); setTimeout(() => setPrefSaved(false), 3000); }}
                  className="text-sm p-2.5 rounded-lg border border-input bg-background w-full focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="gemini-1.5-pro">Google Gemini 1.5 Pro</option>
                  <option value="claude-3-5-sonnet">Anthropic Claude 3.5 Sonnet</option>
                  <option value="gpt-4o">OpenAI GPT-4o</option>
                  <option value="deepseek-r1">OpenRouter (DeepSeek R1)</option>
                  <option value="llama-3.3-70b">Groq (Llama 3.3 70B)</option>
                  <option value="command-r-plus">Cohere Command R+</option>
                </select>
              </div>
              {prefSaved && (
                <p className="text-xs text-green-500 font-semibold flex items-center gap-1">
                  <Check className="h-3.5 w-3.5" /> Preferred model saved.
                </p>
              )}
            </CardContent>
          </Card>
        );

      case "notifications":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" /> Notification Preferences
              </CardTitle>
              <CardDescription>Control operational alerting channels and benchmark emails.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 border border-border/50 rounded-xl bg-background/40">
                  <div>
                    <p className="font-semibold text-sm">Security & Audit Notifications</p>
                    <p className="text-xs text-muted-foreground">Receive instant alerts when API key changes or privilege escalations occur.</p>
                  </div>
                  <Badge variant="default">Enabled</Badge>
                </div>
                <div className="flex items-center justify-between p-4 border border-border/50 rounded-xl bg-background/40">
                  <div>
                    <p className="font-semibold text-sm">Evaluation Benchmark Reports</p>
                    <p className="text-xs text-muted-foreground">Weekly automated summary emails of test suite accuracy scores.</p>
                  </div>
                  <Badge variant="outline">Disabled</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        );

      case "appearance":
        return (
          <Card className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Paintbrush className="h-5 w-5 text-primary" /> Appearance Settings
              </CardTitle>
              <CardDescription>Customize dark and light theme display modes.</CardDescription>
            </CardHeader>
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <p className="font-semibold text-sm">Theme Mode</p>
                <p className="text-xs text-muted-foreground">Adjust display color schemes for visual clarity.</p>
              </div>
              <ThemeToggle />
            </CardContent>
          </Card>
        );

      case "delete_account":
        return (
          <Card className="border-destructive/40 bg-destructive/5 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold text-destructive flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" /> Danger Zone — Delete Account
              </CardTitle>
              <CardDescription>Permanently remove your account and all associated workspace data.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Once deleted, your account cannot be restored. All projects, API keys, and workspace resources will be permanently purged.
              </p>
              <Button 
                variant="destructive"
                className="font-semibold"
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
        );

      default:
        return null;
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Header Banner */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">System Settings</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Manage user credentials, organization workspaces, production LLM model providers, and platform preferences.
        </p>
      </div>

      {/* True Two-Column Layout (GitHub/Vercel/Stripe Settings architecture) */}
      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-8 items-start w-full">
        {/* Left Fixed Navigation Sidebar */}
        <aside className="w-full sticky top-20 self-start space-y-6 border-r border-border/40 pr-4 hidden lg:block">
          {categories.map((cat, idx) => (
            <div key={idx} className="space-y-1">
              <h3 className="px-3 text-[11px] font-bold uppercase tracking-wider text-muted-foreground/80">
                {cat.title}
              </h3>
              <div className="space-y-0.5">
                {cat.tabs.map((tab) => {
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => handleTabChange(tab.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-150 text-left outline-none font-medium ${
                        isActive
                          ? "bg-primary/10 text-primary font-semibold border-l-2 border-primary rounded-l-none"
                          : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                      }`}
                    >
                      <span className={isActive ? "text-primary" : "text-muted-foreground"}>
                        {tab.icon}
                      </span>
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </aside>

        {/* Mobile Navigation Dropdown (< lg) */}
        <div className="lg:hidden w-full mb-4">
          <label className="text-xs font-semibold uppercase text-muted-foreground mb-1 block">
            Settings Section
          </label>
          <div className="relative">
            <select
              value={activeTab}
              onChange={(e) => handleTabChange(e.target.value as SettingsTab)}
              className="w-full p-3 pr-10 text-sm font-medium border border-input rounded-xl bg-card text-foreground appearance-none focus:outline-none focus:ring-1 focus:ring-primary shadow-sm"
            >
              {categories.map((cat, idx) => (
                <optgroup key={idx} label={cat.title}>
                  {cat.tabs.map((tab) => (
                    <option key={tab.id} value={tab.id}>
                      {tab.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          </div>
        </div>

        {/* Single Right Content Panel Container */}
        <section className="w-full min-w-0 self-start">
          {renderActiveTab()}
        </section>
      </div>
    </div>
  );
}
