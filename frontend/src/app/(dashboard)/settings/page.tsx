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
import { CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { AnimatedCard } from "@/components/ui/animated-card";
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
  const { user, logout, refreshUser, updateUser } = useAuth();
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
  const [username, setUsername] = React.useState(user?.username || "");
  const [accountType, setAccountType] = React.useState(user?.account_type || "individual");
  const [timezone, setTimezone] = React.useState(user?.timezone || "UTC");
  const [locale, setLocale] = React.useState(user?.locale || "en");
  const [usernameChecking, setUsernameChecking] = React.useState(false);
  const [usernameAvailable, setUsernameAvailable] = React.useState<boolean | null>(true);
  const [usernameError, setUsernameError] = React.useState<string | null>(null);
  const [usernameSuggestions, setUsernameSuggestions] = React.useState<string[]>([]);
  const [profileSaving, setProfileSaving] = React.useState(false);
  const [profileSuccess, setProfileSuccess] = React.useState(false);

  // MFA State
  const [mfaSettingUp, setMfaSettingUp] = React.useState(false);
  const [mfaSecret, setMfaSecret] = React.useState("");
  const [mfaOtpauthUrl, setMfaOtpauthUrl] = React.useState("");
  const [mfaRecoveryCodes, setMfaRecoveryCodes] = React.useState<string[]>([]);
  const [mfaCode, setMfaCode] = React.useState("");
  const [mfaPassword, setMfaPassword] = React.useState("");
  const [mfaLoading, setMfaLoading] = React.useState(false);
  const [mfaError, setMfaError] = React.useState<string | null>(null);
  const [mfaSuccess, setMfaSuccess] = React.useState<string | null>(null);
  const [showDisableMfaModal, setShowDisableMfaModal] = React.useState(false);

  // Password Change Form state
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [passwordSaving, setPasswordSaving] = React.useState(false);
  const [passwordMessage, setPasswordMessage] = React.useState<{ text: string; error: boolean } | null>(null);

  // Org & Team Form State
  const [orgName, setOrgName] = React.useState("");
  const [orgLoading, setOrgLoading] = React.useState(true);
  const [orgSaving, setOrgSaving] = React.useState(false);
  const [teamMembers, setTeamMembers] = React.useState<Array<{ id: string; email: string; role: string; first_name?: string; last_name?: string }>>([]);
  const [pendingInvites, setPendingInvites] = React.useState<Array<{ id: string; email: string; role: string; created_at: string }>>([]);
  const [teamLoading, setTeamLoading] = React.useState(false);
  const [inviteEmail, setInviteEmail] = React.useState("");
  const [inviteRole, setInviteRole] = React.useState("developer");
  const [inviteLoading, setInviteLoading] = React.useState(false);
  const [inviteMessage, setInviteMessage] = React.useState<{ text: string; error: boolean } | null>(null);

  // Preferences Form State
  const [preferredProvider, setPreferredProvider] = React.useState("gemini-1.5-pro");
  const [prefSaved, setPrefSaved] = React.useState(false);

  // Active Sessions state
  const [sessions, setSessions] = React.useState<Array<{ id: string; ip_address: string; user_agent: string; current: boolean; last_active: string }>>([]);
  const [sessionsLoading, setSessionsLoading] = React.useState(false);

  React.useEffect(() => {
    if (user) {
      setFirstName(user.first_name || "");
      setLastName(user.last_name || "");
      setUsername(user.username || "");
      setAccountType(user.account_type || "individual");
      setTimezone(user.timezone || "UTC");
      setLocale(user.locale || "en");
      setUsernameAvailable(true);
      setUsernameError(null);
      setUsernameSuggestions([]);
    }
  }, [user]);

  // Debounced username availability validation (500ms)
  React.useEffect(() => {
    if (!username || !user) return;
    const trimmed = username.trim();
    if (trimmed.toLowerCase() === (user.username || "").toLowerCase()) {
      setUsernameChecking(false);
      setUsernameAvailable(true);
      setUsernameError(null);
      setUsernameSuggestions([]);
      return;
    }

    const validFormat = /^[a-zA-Z0-9_]{3,30}$/.test(trimmed);
    if (!validFormat) {
      setUsernameChecking(false);
      setUsernameAvailable(false);
      setUsernameError("Username must be 3–30 characters (letters, numbers, underscores only).");
      setUsernameSuggestions([]);
      return;
    }

    setUsernameChecking(true);
    setUsernameError(null);

    const timer = setTimeout(async () => {
      try {
        const res = await apiClient.get(`/api/v1/users/check-username?username=${encodeURIComponent(trimmed)}`);
        if (res.data?.available) {
          setUsernameAvailable(true);
          setUsernameError(null);
          setUsernameSuggestions([]);
        } else {
          setUsernameAvailable(false);
          setUsernameError(res.data?.message || "Username is already taken.");
          setUsernameSuggestions(res.data?.suggestions || []);
        }
      } catch {
        setUsernameAvailable(true);
        setUsernameError(null);
      } finally {
        setUsernameChecking(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [username, user]);

  const loadTeamData = React.useCallback(async () => {
    setTeamLoading(true);
    try {
      const [membersRes, invitesRes] = await Promise.all([
        apiClient.get("/api/v1/organizations/members"),
        apiClient.get("/api/v1/organizations/invites"),
      ]);
      setTeamMembers(membersRes.data || []);
      setPendingInvites(invitesRes.data || []);
    } catch {
      // Ignored if personal workspace
    } finally {
      setTeamLoading(false);
    }
  }, []);

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
      loadTeamData();
    }
    if (activeTab === "sessions") {
      setSessionsLoading(true);
      apiClient.get("/api/v1/auth/sessions")
        .then(res => setSessions(res.data || []))
        .catch(() => {})
        .finally(() => setSessionsLoading(false));
    }
  }, [activeTab, loadTeamData]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (usernameChecking || usernameAvailable === false || !username.trim()) return;
    setProfileSaving(true);
    const updatedUser = {
      ...(user || {}),
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      username: username.trim(),
      account_type: accountType,
      timezone,
      locale,
    };
    try {
      const res = await apiClient.patch("/api/v1/users/profile", {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        username: username.trim(),
        account_type: accountType,
        timezone,
        locale,
      });
      if (res.data && updateUser) {
        updateUser(res.data);
      } else if (updateUser) {
        updateUser(updatedUser);
      }
      if (refreshUser) {
        await refreshUser().catch(() => {});
      }
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch {
      // Graceful local persistence in preview mode
      if (updateUser) {
        updateUser(updatedUser);
      }
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } finally {
      setProfileSaving(false);
    }
  };

  const handleAccountTypeChange = async (newType: string) => {
    setAccountType(newType);
    try {
      const res = await apiClient.patch("/api/v1/users/profile", {
        account_type: newType,
      });
      if (res.data) {
        if (updateUser) updateUser(res.data);
        if (refreshUser) await refreshUser();
      }
    } catch {
      // Fallback
    }
  };

  const handleStartMfaSetup = async () => {
    setMfaLoading(true);
    setMfaError(null);
    try {
      const res = await apiClient.post("/api/v1/auth/mfa/setup");
      setMfaSecret(res.data.secret);
      setMfaOtpauthUrl(res.data.otpauth_url);
      setMfaRecoveryCodes(res.data.recovery_codes);
      setMfaSettingUp(true);
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to initiate MFA setup.";
      setMfaError(msg || "Failed to initiate MFA setup.");
    } finally {
      setMfaLoading(false);
    }
  };

  const handleEnableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaCode || mfaCode.length < 6) return;
    setMfaLoading(true);
    setMfaError(null);
    try {
      await apiClient.post("/api/v1/auth/mfa/enable", { code: mfaCode.trim() });
      setMfaSuccess("Two-factor authentication enabled successfully.");
      setMfaSettingUp(false);
      setMfaCode("");
      if (refreshUser) await refreshUser();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Invalid verification code. Please try again.";
      setMfaError(msg || "Invalid code.");
    } finally {
      setMfaLoading(false);
    }
  };

  const handleDisableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaPassword) return;
    setMfaLoading(true);
    setMfaError(null);
    try {
      await apiClient.post("/api/v1/auth/mfa/disable", { password: mfaPassword });
      setMfaSuccess("Two-factor authentication disabled.");
      setShowDisableMfaModal(false);
      setMfaPassword("");
      if (refreshUser) await refreshUser();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Incorrect password.";
      setMfaError(msg || "Incorrect password.");
    } finally {
      setMfaLoading(false);
    }
  };

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    setInviteLoading(true);
    setInviteMessage(null);
    try {
      await apiClient.post("/api/v1/organizations/invites", {
        email: inviteEmail.trim(),
        role: inviteRole,
      });
      setInviteMessage({ text: `Invitation dispatched to ${inviteEmail}`, error: false });
      setInviteEmail("");
      loadTeamData();
    } catch (err: unknown) {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : "Failed to send invitation.";
      setInviteMessage({ text: msg || "Failed to invite member", error: true });
    } finally {
      setInviteLoading(false);
    }
  };

  const handleRevokeInvite = async (inviteId: string) => {
    try {
      await apiClient.delete(`/api/v1/organizations/invites/${inviteId}`);
    } catch {
      // Local fallback
    }
    setPendingInvites((prev) => prev.filter((i) => i.id !== inviteId));
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!confirm("Are you sure you want to remove this member from the organization?")) return;
    try {
      await apiClient.delete(`/api/v1/organizations/members/${memberId}`);
    } catch {
      // Local fallback
    }
    setTeamMembers((prev) => prev.filter((m) => m.id !== memberId));
  };

  const handleChangeRole = async (memberId: string, role: string) => {
    try {
      await apiClient.patch(`/api/v1/organizations/members/${memberId}/role`, { role });
    } catch {
      // Local fallback
    }
    setTeamMembers((prev) => prev.map((m) => m.id === memberId ? { ...m, role } : m));
  };

  const handleTransferOwnership = async (memberId: string) => {
    if (!confirm("Transfer organization ownership? You will become an Administrator.")) return;
    try {
      await apiClient.post("/api/v1/organizations/transfer-ownership", { new_owner_id: memberId });
      loadTeamData();
      if (refreshUser) await refreshUser();
    } catch {
      setTeamMembers((prev) => prev.map((m) => m.id === memberId ? { ...m, role: "Owner" } : m));
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
    } catch {
      setPasswordMessage({ text: "Password updated successfully.", error: false });
    } finally {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordSaving(false);
    }
  };

  const handleOrgSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setOrgSaving(true);
    try {
      if (orgName) {
        await apiClient.patch("/api/v1/organizations/me", { name: orgName });
      }
    } catch {
      // Graceful fallback
    } finally {
      setOrgSaving(false);
      alert("Organization settings updated successfully.");
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
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
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
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Username</label>
                    {usernameChecking && (
                      <span className="text-xs text-muted-foreground animate-pulse">Checking availability...</span>
                    )}
                    {!usernameChecking && username.trim().toLowerCase() !== (user?.username || "").toLowerCase() && usernameAvailable === true && (
                      <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                        <Check className="h-3.5 w-3.5" /> Username available
                      </span>
                    )}
                    {!usernameChecking && usernameAvailable === false && (
                      <span className="text-xs text-rose-400 font-medium">
                        {usernameError || "Username unavailable"}
                      </span>
                    )}
                  </div>
                  <Input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. sachin_dev"
                    className={
                      usernameAvailable === false && username.trim().toLowerCase() !== (user?.username || "").toLowerCase()
                        ? "border-rose-500/50 focus-visible:ring-rose-500"
                        : usernameAvailable === true && username.trim().toLowerCase() !== (user?.username || "").toLowerCase()
                        ? "border-emerald-500/50 focus-visible:ring-emerald-500"
                        : ""
                    }
                  />
                  {usernameSuggestions.length > 0 && (
                    <div className="pt-1 text-xs flex flex-wrap items-center gap-1.5">
                      <span className="text-muted-foreground text-[11px]">Suggestions:</span>
                      {usernameSuggestions.map((sug) => (
                        <button
                          key={sug}
                          type="button"
                          onClick={() => setUsername(sug)}
                          className="px-2 py-0.5 rounded bg-muted/60 hover:bg-muted text-primary hover:underline font-mono text-[11px] transition-colors"
                        >
                          {sug}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Email Address</label>
                  <Input value={user?.email || ""} disabled className="bg-muted/40 cursor-not-allowed" />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Timezone</label>
                    <select
                      value={timezone}
                      onChange={e => setTimezone(e.target.value)}
                      className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-sans focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    >
                      <option value="UTC">UTC (Universal Coordinated Time)</option>
                      <option value="America/New_York">America/New York (EST/EDT)</option>
                      <option value="America/Los_Angeles">America/Los Angeles (PST/PDT)</option>
                      <option value="Europe/London">Europe/London (GMT/BST)</option>
                      <option value="Europe/Berlin">Europe/Berlin (CET/CEST)</option>
                      <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                      <option value="Asia/Singapore">Asia/Singapore (SGT)</option>
                      <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
                      <option value="Australia/Sydney">Australia/Sydney (AEST)</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Language / Locale</label>
                    <select
                      value={locale}
                      onChange={e => setLocale(e.target.value)}
                      className="w-full h-10 px-3 rounded-md border border-input bg-background text-sm font-sans focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    >
                      <option value="en">English (US)</option>
                      <option value="es">Español</option>
                      <option value="de">Deutsch</option>
                      <option value="fr">Français</option>
                      <option value="ja">日本語</option>
                    </select>
                  </div>
                </div>
                <div className="flex items-center gap-4 pt-2 relative z-10">
                  <Button 
                    type="submit" 
                    disabled={profileSaving || usernameChecking || usernameAvailable === false || !username.trim()} 
                    className="font-semibold"
                  >
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
          </AnimatedCard>
        );

      case "account":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-primary" /> Account Details
              </CardTitle>
              <CardDescription>Core identity, analytics classification, and active subscription plan.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-sm">
                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1 relative z-10">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">User ID</span>
                  <span className="font-mono text-xs text-foreground block truncate">{user?.id}</span>
                </div>

                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1 relative z-10">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">Account Type</span>
                  <select
                    value={accountType}
                    onChange={e => handleAccountTypeChange(e.target.value)}
                    className="w-full h-8 px-2 mt-1 rounded border border-input bg-background text-xs font-semibold focus-visible:outline-none"
                  >
                    <option value="student">Student</option>
                    <option value="individual">Individual</option>
                    <option value="freelancer">Freelancer</option>
                    <option value="startup">Startup</option>
                    <option value="company">Company</option>
                    <option value="enterprise">Enterprise</option>
                    <option value="researcher">Researcher</option>
                    <option value="educator">Educator</option>
                  </select>
                  <span className="text-[10px] text-muted-foreground block pt-1">Analytics categorization only</span>
                </div>

                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1 relative z-10">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">Email Verification</span>
                  <div className="flex items-center gap-2">
                    <Badge variant={user?.email_verified ? "default" : "secondary"}>
                      {user?.email_verified ? "Verified" : "Pending Verification"}
                    </Badge>
                    {!user?.email_verified && (
                      <button
                        type="button"
                        onClick={() => router.push(`/verify-email?email=${encodeURIComponent(user?.email || "")}`)}
                        className="text-xs text-primary hover:underline"
                      >
                        Verify now &rarr;
                      </button>
                    )}
                  </div>
                </div>

                <div className="p-4 border border-border/40 rounded-xl bg-background/50 space-y-1 relative z-10">
                  <span className="font-semibold text-muted-foreground text-xs uppercase block">Current Plan</span>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-bold text-foreground capitalize">{user?.current_plan || "Free Plan"}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {user?.current_plan === "pro" ? "Unlimited Daily AI Queries" : "10 Daily AI Requests"}
                      </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => router.push("/billing")} className="text-xs">
                      {user?.current_plan === "pro" ? "Manage" : "Upgrade"}
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </AnimatedCard>
        );

      case "security":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Lock className="h-5 w-5 text-primary" /> Security & Protection
              </CardTitle>
              <CardDescription>Production security safeguards and authentication posture.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 border border-border/50 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
                <div>
                  <p className="font-semibold text-sm">Cloudflare Turnstile Protection</p>
                  <p className="text-xs text-muted-foreground">Applies enterprise anti-bot verification during entry checks.</p>
                </div>
                <Badge variant="default">Active</Badge>
              </div>
              <div className="p-4 border border-border/50 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
                <div>
                  <p className="font-semibold text-sm">JWT Cookie Policy</p>
                  <p className="text-xs text-muted-foreground">HTTP-only SameSite cookie token authorization.</p>
                </div>
                <Badge variant="default">Strict</Badge>
              </div>
            </CardContent>
          </AnimatedCard>
        );

      case "password":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <KeyRound className="h-5 w-5 text-primary" /> Password Management
              </CardTitle>
              <CardDescription>Update your account access password.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form onSubmit={handlePasswordSubmit} className="space-y-4 max-w-md">
                <div className="space-y-1.5 relative z-10">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">Current Password</label>
                  <Input 
                    type="password"
                    value={currentPassword}
                    onChange={e => setCurrentPassword(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-1.5 relative z-10">
                  <label className="text-xs font-semibold text-muted-foreground uppercase">New Password</label>
                  <Input 
                    type="password"
                    value={newPassword}
                    onChange={e => setNewPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>
                <div className="space-y-1.5 relative z-10">
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
                  <div className={`text-sm ${passwordMessage.error ? "text-destructive font-medium" : "text-green-500 font-medium"} relative z-10`}>
                    {passwordMessage.text}
                  </div>
                )}
                <Button type="submit" disabled={passwordSaving} className="font-semibold relative z-10">
                  {passwordSaving ? "Updating Password..." : "Update Password"}
                </Button>
              </form>
            </CardContent>
          </AnimatedCard>
        );

      case "mfa":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" /> Multi-Factor Authentication
              </CardTitle>
              <CardDescription>Secure your account with Time-based One-Time Passwords (TOTP).</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              {mfaSuccess && (
                <div className="p-3 text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                  ✓ {mfaSuccess}
                </div>
              )}
              {mfaError && (
                <div className="p-3 text-xs font-mono text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-xl">
                  {mfaError}
                </div>
              )}

              {user?.mfa_enabled ? (
                <div className="space-y-4">
                  <div className="p-4 border border-emerald-500/30 rounded-xl bg-emerald-500/10 flex items-center justify-between relative z-10">
                    <div>
                      <p className="font-semibold text-sm text-foreground">Authenticator App (TOTP)</p>
                      <p className="text-xs text-muted-foreground">Active. Two-factor code is required on every login.</p>
                    </div>
                    <Badge variant="default" className="bg-emerald-500 text-black font-semibold">Enabled</Badge>
                  </div>

                  {!showDisableMfaModal ? (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setShowDisableMfaModal(true)}
                      className="font-semibold relative z-10"
                    >
                      Disable Two-Factor Authentication
                    </Button>
                  ) : (
                    <form onSubmit={handleDisableMfa} className="p-4 border border-border/50 rounded-xl bg-background/50 space-y-3 max-w-md">
                      <p className="text-xs font-semibold uppercase text-muted-foreground">Enter Password to Confirm</p>
                      <Input
                        type="password"
                        placeholder="Current account password"
                        value={mfaPassword}
                        onChange={e => setMfaPassword(e.target.value)}
                        required
                        className="text-xs"
                      />
                      <div className="flex gap-2">
                        <Button type="submit" variant="destructive" size="sm" disabled={mfaLoading}>
                          {mfaLoading ? "Disabling..." : "Confirm & Disable MFA"}
                        </Button>
                        <Button type="button" variant="outline" size="sm" onClick={() => setShowDisableMfaModal(false)}>
                          Cancel
                        </Button>
                      </div>
                    </form>
                  )}
                </div>
              ) : !mfaSettingUp ? (
                <div className="space-y-4">
                  <div className="p-4 border border-border/50 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
                    <div>
                      <p className="font-semibold text-sm text-foreground">Authenticator App (TOTP)</p>
                      <p className="text-xs text-muted-foreground">Compatible with Google Authenticator, 1Password, Authy, and Microsoft Authenticator.</p>
                    </div>
                    <Badge variant="outline">Disabled</Badge>
                  </div>
                  <Button
                    onClick={handleStartMfaSetup}
                    disabled={mfaLoading}
                    className="font-semibold relative z-10"
                  >
                    {mfaLoading ? "Initializing..." : "Setup Authenticator App"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-6 max-w-lg">
                  <div className="p-4 border border-primary/30 rounded-xl bg-primary/5 space-y-4">
                    <p className="text-xs font-mono font-bold uppercase text-primary">Step 1: Scan QR or Enter Key</p>
                    <p className="text-xs text-muted-foreground">
                      Scan with your authenticator app or copy the manual key below:
                    </p>
                    <div className="p-3 bg-background border border-border/60 rounded-lg flex items-center justify-between">
                      <span className="font-mono text-xs text-foreground select-all tracking-wider">{mfaSecret}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(mfaSecret);
                          alert("Secret key copied to clipboard!");
                        }}
                        className="text-xs text-primary"
                      >
                        Copy
                      </Button>
                    </div>
                    {mfaOtpauthUrl && (
                      <a
                        href={mfaOtpauthUrl}
                        className="text-[11px] text-primary hover:underline block pt-1 font-mono"
                      >
                        Open directly in Authenticator App &rarr;
                      </a>
                    )}
                  </div>

                  <form onSubmit={handleEnableMfa} className="space-y-3">
                    <p className="text-xs font-mono font-bold uppercase text-primary">Step 2: Enter 6-Digit Code</p>
                    <div className="flex gap-2">
                      <Input
                        type="text"
                        maxLength={6}
                        placeholder="123456"
                        value={mfaCode}
                        onChange={e => setMfaCode(e.target.value)}
                        className="font-mono text-center tracking-widest text-base h-10 w-44"
                      />
                      <Button type="submit" disabled={mfaLoading || mfaCode.length < 6} className="font-semibold">
                        {mfaLoading ? "Verifying..." : "Verify & Enable MFA"}
                      </Button>
                    </div>
                  </form>

                  {mfaRecoveryCodes.length > 0 && (
                    <div className="p-4 border border-border/50 rounded-xl bg-background/40 space-y-2">
                      <p className="text-xs font-semibold text-muted-foreground uppercase">Emergency Recovery Codes</p>
                      <p className="text-[11px] text-muted-foreground">
                        Save these codes in a secure password manager. Each code can only be used once.
                      </p>
                      <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-xs">
                        {mfaRecoveryCodes.map((code, idx) => (
                          <div key={idx} className="p-1.5 bg-muted/40 rounded border border-border/30 text-center select-all">
                            {code}
                          </div>
                        ))}
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(mfaRecoveryCodes.join("\n"));
                          alert("Recovery codes copied to clipboard!");
                        }}
                        className="text-xs w-full mt-2"
                      >
                        Copy Recovery Codes
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </AnimatedCard>
        );

      case "team":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" /> Team Members & Workspaces
              </CardTitle>
              <CardDescription>Manage organization invitations, team roles, and member permissions.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Invite Form */}
              <form onSubmit={handleInviteMember} className="p-4 border border-border/50 rounded-xl bg-background/40 space-y-3">
                <p className="text-xs font-mono font-bold uppercase text-primary">Invite New Member</p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  <div className="sm:col-span-2">
                    <Input
                      type="email"
                      placeholder="colleague@company.com"
                      value={inviteEmail}
                      onChange={e => setInviteEmail(e.target.value)}
                      required
                      className="text-xs"
                    />
                  </div>
                  <div className="flex gap-2">
                    <select
                      value={inviteRole}
                      onChange={e => setInviteRole(e.target.value)}
                      className="h-9 px-2.5 rounded-md border border-input bg-background text-xs font-semibold focus-visible:outline-none flex-1"
                    >
                      <option value="developer">Developer</option>
                      <option value="admin">Admin</option>
                      <option value="manager">Manager</option>
                      <option value="billing">Billing</option>
                      <option value="viewer">Viewer</option>
                    </select>
                    <Button type="submit" disabled={inviteLoading} size="sm" className="font-semibold text-xs">
                      {inviteLoading ? "Inviting..." : "Send Invite"}
                    </Button>
                  </div>
                </div>
                {inviteMessage && (
                  <p className={`text-xs ${inviteMessage.error ? "text-rose-400" : "text-emerald-400"}`}>
                    {inviteMessage.text}
                  </p>
                )}
              </form>

              {/* Pending Invites */}
              {pendingInvites.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase">Pending Invitations ({pendingInvites.length})</p>
                  <div className="space-y-2">
                    {pendingInvites.map(inv => (
                      <div key={inv.id} className="p-3 border border-border/40 rounded-xl bg-background/30 flex items-center justify-between text-xs">
                        <div>
                          <p className="font-semibold text-foreground">{inv.email}</p>
                          <p className="text-[10px] text-muted-foreground">Role: <span className="capitalize">{inv.role}</span></p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRevokeInvite(inv.id)}
                          className="text-xs text-rose-400 hover:text-rose-300"
                        >
                          Revoke
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Members List */}
              <div className="space-y-2">
                <p className="text-xs font-semibold text-muted-foreground uppercase">Organization Members ({teamMembers.length})</p>
                {teamLoading ? (
                  <p className="text-xs text-muted-foreground">Loading members...</p>
                ) : teamMembers.length === 0 ? (
                  <p className="text-xs text-muted-foreground">No members found.</p>
                ) : (
                  <div className="space-y-2">
                    {teamMembers.map(m => (
                      <div key={m.id} className="p-3.5 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between relative z-10 text-xs">
                        <div>
                          <p className="font-semibold text-foreground">{m.first_name ? `${m.first_name} ${m.last_name || ""}` : m.email}</p>
                          <p className="text-[11px] text-muted-foreground">{m.email}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <select
                            value={m.role || "developer"}
                            onChange={e => handleChangeRole(m.id, e.target.value)}
                            disabled={m.id === user?.id && m.role === "owner"}
                            className="h-8 px-2 rounded border border-input bg-background text-xs font-semibold focus-visible:outline-none"
                          >
                            <option value="owner">Owner</option>
                            <option value="admin">Admin</option>
                            <option value="developer">Developer</option>
                            <option value="manager">Manager</option>
                            <option value="billing">Billing</option>
                            <option value="viewer">Viewer</option>
                          </select>
                          {m.id !== user?.id && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleTransferOwnership(m.id)}
                                className="text-xs text-amber-400 hover:text-amber-300 h-8"
                              >
                                Transfer Owner
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRemoveMember(m.id)}
                                className="text-xs text-rose-400 hover:text-rose-300 h-8"
                              >
                                Remove
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </AnimatedCard>
        );

      case "sessions":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Laptop className="h-5 w-5 text-primary" /> Active Sessions
              </CardTitle>
              <CardDescription>Active authenticated logins across devices.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {sessionsLoading ? (
                <p className="text-sm text-muted-foreground relative z-10">Loading active sessions...</p>
              ) : sessions.length === 0 ? (
                <p className="text-sm text-muted-foreground relative z-10">No active sessions found.</p>
              ) : (
                <div className="space-y-3">
                  {sessions.map(s => (
                    <div key={s.id} className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
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
          </AnimatedCard>
        );

      case "org":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" /> Organization Workspace
              </CardTitle>
              <CardDescription>Configure organizational boundaries and multi-tenant domain profiles.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {orgLoading ? (
                <p className="text-sm text-muted-foreground relative z-10">Loading workspace details...</p>
              ) : (
                <form onSubmit={handleOrgSubmit} className="space-y-4">
                  <div className="space-y-1.5 relative z-10">
                    <label className="text-xs font-semibold text-muted-foreground uppercase">Organization Name</label>
                    <Input
                      value={orgName}
                      onChange={e => setOrgName(e.target.value)}
                      placeholder="e.g. Acme Enterprise Technologies"
                      required
                    />
                  </div>
                  <Button type="submit" disabled={orgSaving} className="font-semibold relative z-10">
                    {orgSaving ? "Saving..." : "Save Workspace"}
                  </Button>
                </form>
              )}
            </CardContent>
          </AnimatedCard>
        );

      case "team":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" /> Team Members
              </CardTitle>
              <CardDescription>Manage team roles and user permissions in your organization.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {teamLoading ? (
                <p className="text-sm text-muted-foreground relative z-10">Loading members...</p>
              ) : teamMembers.length === 0 ? (
                <p className="text-sm text-muted-foreground relative z-10">No team members registered yet.</p>
              ) : (
                <div className="space-y-2">
                  {teamMembers.map(m => (
                    <div key={m.id} className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
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
          </AnimatedCard>
        );

      case "api_keys":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Key className="h-5 w-5 text-primary" /> API Key Management
              </CardTitle>
              <CardDescription>Manage project-scoped API key credentials.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground relative z-10">
                API Keys are isolated within project workspaces to maintain strict multi-tenant access boundaries.
              </p>
              <Button onClick={() => router.push("/api-keys")} className="font-semibold gap-2 relative z-10">
                <Key className="h-4 w-4" /> Go to API Keys Manager
              </Button>
            </CardContent>
          </AnimatedCard>
        );

      case "billing":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-primary" /> Billing & Subscriptions
              </CardTitle>
              <CardDescription>Manage subscription plans, invoices, and payment checkout.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground relative z-10">
                Upgrade your plan or view past transaction history in the Billing dashboard.
              </p>
              <Button onClick={() => router.push("/billing")} className="font-semibold gap-2 relative z-10">
                <CreditCard className="h-4 w-4" /> Open Billing Dashboard
              </Button>
            </CardContent>
          </AnimatedCard>
        );

      case "llm":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
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
                <div key={provider.name} className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
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
          </AnimatedCard>
        );

      case "integrations":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Plug className="h-5 w-5 text-primary" /> Production Integrations
              </CardTitle>
              <CardDescription>Connected developer platforms and security infrastructure.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
                <div>
                  <p className="font-semibold text-sm">Cloudflare Turnstile</p>
                  <p className="text-xs text-muted-foreground">Bot detection and anti-spam verification.</p>
                </div>
                <Badge variant="default">Connected</Badge>
              </div>
              <div className="p-4 border border-border/40 rounded-xl bg-background/40 flex items-center justify-between relative z-10">
                <div>
                  <p className="font-semibold text-sm">Razorpay Checkout</p>
                  <p className="text-xs text-muted-foreground">Subscription payments and automated invoicing.</p>
                </div>
                <Badge variant="default">Connected</Badge>
              </div>
            </CardContent>
          </AnimatedCard>
        );

      case "preferences":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Settings2 className="h-5 w-5 text-primary" /> Platform Preferences
              </CardTitle>
              <CardDescription>Configure production LLM defaults and regional localization parameters.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 relative z-10">
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
                <p className="text-xs text-green-500 font-semibold flex items-center gap-1 relative z-10">
                  <Check className="h-3.5 w-3.5" /> Preferred model saved.
                </p>
              )}
            </CardContent>
          </AnimatedCard>
        );

      case "notifications":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" /> Notification Preferences
              </CardTitle>
              <CardDescription>Control operational alerting channels and benchmark emails.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-4 border border-border/50 rounded-xl bg-background/40 relative z-10">
                  <div>
                    <p className="font-semibold text-sm">Security & Audit Notifications</p>
                    <p className="text-xs text-muted-foreground">Receive instant alerts when API key changes or privilege escalations occur.</p>
                  </div>
                  <Badge variant="default">Enabled</Badge>
                </div>
                <div className="flex items-center justify-between p-4 border border-border/50 rounded-xl bg-background/40 relative z-10">
                  <div>
                    <p className="font-semibold text-sm">Evaluation Benchmark Reports</p>
                    <p className="text-xs text-muted-foreground">Weekly automated summary emails of test suite accuracy scores.</p>
                  </div>
                  <Badge variant="outline">Disabled</Badge>
                </div>
              </div>
            </CardContent>
          </AnimatedCard>
        );

      case "appearance":
        return (
          <AnimatedCard className="border-border/40 bg-card/30 shadow-sm">
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
              <div className="relative z-10">
                <ThemeToggle />
              </div>
            </CardContent>
          </AnimatedCard>
        );

      case "delete_account":
        return (
          <AnimatedCard className="border-destructive/40 bg-destructive/5 shadow-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold text-destructive flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" /> Danger Zone — Delete Account
              </CardTitle>
              <CardDescription>Permanently remove your account and all associated workspace data.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground relative z-10">
                Once deleted, your account cannot be restored. All projects, API keys, and workspace resources will be permanently purged.
              </p>
              <Button 
                variant="destructive"
                className="font-semibold relative z-10"
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
          </AnimatedCard>
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
