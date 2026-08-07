"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Cpu, Eye, EyeOff, RefreshCw, Loader2, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Turnstile, TurnstileRef } from "@/components/auth/turnstile";
import { GuestRoute } from "@/components/auth/guest-route";
import { env } from "@/lib/config/env";

const signupSchema = z
  .object({
    workspaceName: z.string().min(1, "Workspace Name is required"),
    fullName: z.string().min(1, "Full Name is required"),
    email: z.string().email("Invalid email address"),
    password: z
      .string()
      .min(12, "Password must be at least 12 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/\d/, "Password must contain at least one number")
      .regex(/[^A-Za-z0-9]/, "Password must contain at least one special character"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
    acceptTerms: z.boolean().refine((val) => val === true, {
      message: "You must accept the terms and conditions",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Confirm password does not match the entered password",
    path: ["confirmPassword"],
  });

type SignupValues = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);
  const [captchaError, setCaptchaError] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const turnstileRef = React.useRef<TurnstileRef>(null);
  const pendingValuesRef = React.useRef<SignupValues | null>(null);
  const [oauthLoading, setOauthLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [duplicateEmailToast, setDuplicateEmailToast] = React.useState<{ show: boolean; email: string } | null>(null);

  const handleOAuthLogin = async (provider: "github" | "google") => {
    setOauthLoading(true);
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/oauth/${provider}`, {
        credentials: "include",
      });
      const data = await response.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError(`${provider} login is not configured on this server.`);
        setOauthLoading(false);
      }
    } catch {
      setError(`Failed to initiate ${provider} login.`);
      setOauthLoading(false);
    }
  };

  const handleGithubLogin = () => handleOAuthLogin("github");
  const handleGoogleLogin = () => handleOAuthLogin("google");

  const form = useForm<SignupValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      workspaceName: "",
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptTerms: false,
    },
  });

  const watchPassword = form.watch("password", "");

  const rules = {
    length: watchPassword.length >= 12,
    uppercase: /[A-Z]/.test(watchPassword),
    lowercase: /[a-z]/.test(watchPassword),
    number: /\d/.test(watchPassword),
    special: /[^A-Za-z0-9]/.test(watchPassword),
  };

  const getStrength = (): { score: number; label: string; color: string } => {
    if (!watchPassword) return { score: 0, label: "None", color: "bg-[#202833]" };
    let score = 0;
    if (rules.length) score += 1;
    if (rules.uppercase) score += 1;
    if (rules.lowercase) score += 1;
    if (rules.number) score += 1;
    if (rules.special) score += 1;

    switch (score) {
      case 1:
      case 2:
        return { score: 40, label: "Weak", color: "bg-[#F05252]" };
      case 3:
        return { score: 60, label: "Medium", color: "bg-[#F5B942]" };
      case 4:
        return { score: 80, label: "Strong", color: "bg-[#38BDF8]" };
      case 5:
        return { score: 100, label: "Excellent", color: "bg-[#2DD4A3]" };
      default:
        return { score: 20, label: "Weak", color: "bg-[#F05252]" };
    }
  };

  const strength = getStrength();

  const generatePassword = () => {
    const uppercaseChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const lowercaseChars = "abcdefghijklmnopqrstuvwxyz";
    const numberChars = "0123456789";
    const specialChars = "!@#$%^&*()_+~`|}{[]:;?><,./-=";
    const allChars = uppercaseChars + lowercaseChars + numberChars + specialChars;
    
    let newPassword = "";
    newPassword += uppercaseChars[Math.floor(Math.random() * uppercaseChars.length)];
    newPassword += lowercaseChars[Math.floor(Math.random() * lowercaseChars.length)];
    newPassword += numberChars[Math.floor(Math.random() * numberChars.length)];
    newPassword += specialChars[Math.floor(Math.random() * specialChars.length)];
    
    for (let i = 0; i < 12; i++) {
      newPassword += allChars[Math.floor(Math.random() * allChars.length)];
    }
    
    form.setValue("password", newPassword, { shouldValidate: true });
    form.setValue("confirmPassword", newPassword, { shouldValidate: true });
  };

  const onSubmit = async (values: SignupValues) => {
    if (isSubmitting) return;
    setCaptchaError("");
    setError("");

    pendingValuesRef.current = values;
    setIsSubmitting(true);

    if (!env.NEXT_PUBLIC_ENABLE_TURNSTILE) {
      handleToken("mock-turnstile-token");
      return;
    }

    turnstileRef.current?.execute();
  };

  const handleToken = React.useCallback(async (freshToken: string) => {
    const values = pendingValuesRef.current;
    if (!values) {
      setIsSubmitting(false);
      turnstileRef.current?.reset();
      return;
    }

    const nameParts = values.fullName.trim().split(" ");
    const firstName = nameParts[0] || "";
    const lastName = nameParts.slice(1).join(" ") || "User";

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          firstName,
          lastName,
          company: values.workspaceName || null,
          email: values.email,
          password: values.password,
          acceptTerms: values.acceptTerms,
          captchaToken: freshToken,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        const detailStr = (errorData && typeof errorData.detail === "string")
          ? errorData.detail.toLowerCase().trim()
          : "";

        if (detailStr.includes("already registered")) {
          setDuplicateEmailToast({ show: true, email: values.email });
          setTimeout(() => {
            router.push(`/login?email=${encodeURIComponent(values.email)}`);
          }, 2000);
          return;
        }

        setCaptchaError(errorData.detail || "Registration failed. Please verify your entries.");
        turnstileRef.current?.reset();
        setIsSubmitting(false);
        return;
      }

      pendingValuesRef.current = null;
      router.push(`/verify-email?email=${encodeURIComponent(values.email)}`);
    } catch {
      setCaptchaError("Unable to connect to the authentication server.");
      turnstileRef.current?.reset();
      setIsSubmitting(false);
    }
  }, [router]);

  const handleTurnstileError = React.useCallback(() => {
    setCaptchaError("Human verification failed. Please try again.");
    turnstileRef.current?.reset();
    setIsSubmitting(false);
  }, []);

  const handleTurnstileExpire = React.useCallback(() => {
    setCaptchaError("Verification expired. Please click Register again.");
    setIsSubmitting(false);
  }, []);

  return (
    <GuestRoute>
      <div className="flex h-screen w-full bg-[#090B0F] text-[#F5F7FA] overflow-hidden">
        {/* Left Side: Auth Form */}
        <div className="flex-1 flex items-center justify-center px-6 lg:px-12 py-10 z-10 overflow-y-auto">
          <Card className="w-full max-w-md border border-[#202833] bg-[#0D1117] shadow-2xl">
            <CardHeader className="text-center pb-3">
              <Link href="/" className="flex items-center justify-center space-x-2.5 mb-2 group">
                <div className="p-1.5 rounded bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/50 transition-colors">
                  <Cpu className="h-5 w-5" />
                </div>
                <span className="font-mono font-bold tracking-wider text-lg text-[#F5F7FA]">ASEP</span>
              </Link>
              <CardTitle className="text-xl font-bold font-mono text-[#F5F7FA]">Create your Account</CardTitle>
              <CardDescription className="text-xs text-[#9CA6B5] font-sans">
                Start orchestrating autonomous software engineering agent collectives.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="mb-4 text-xs font-mono text-[#F05252] bg-[#F05252]/10 rounded border border-[#F05252]/20 p-2 text-center">{error}</div>
              )}
              
              <div className="space-y-2.5 mb-5">
                <button
                  type="button"
                  id="github-oauth-btn"
                  onClick={handleGithubLogin}
                  disabled={oauthLoading}
                  className="w-full flex items-center justify-center gap-2.5 px-4 py-2 rounded border border-[#202833] bg-[#111720] hover:bg-[#111720]/80 transition-all text-xs font-mono text-[#F5F7FA] disabled:opacity-60 h-10"
                >
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  Continue with GitHub
                </button>
                <button
                  type="button"
                  id="google-oauth-btn"
                  onClick={handleGoogleLogin}
                  disabled={oauthLoading}
                  className="w-full flex items-center justify-center gap-2.5 px-4 py-2 rounded border border-[#202833] bg-[#111720] hover:bg-[#111720]/80 transition-all text-xs font-mono text-[#F5F7FA] disabled:opacity-60 h-10"
                >
                  <svg className="h-4 w-4" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continue with Google
                </button>
              </div>

              <div className="relative my-4.5">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-[#202833]" />
                </div>
                <div className="relative flex justify-center text-[10px] uppercase font-mono">
                  <span className="bg-[#0D1117] px-2 text-[#667085]">or register with email</span>
                </div>
              </div>

              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3">
                  <FormField
                    control={form.control}
                    name="workspaceName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Workspace Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Acme Corp" className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] h-9 text-xs" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="fullName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Full Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Jane Doe" className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] h-9 text-xs" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Work Email</FormLabel>
                        <FormControl>
                          <Input
                            type="email"
                            placeholder="jane@company.com"
                            autoComplete="email"
                            className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] h-9 text-xs"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex justify-between items-center">
                          <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Password</FormLabel>
                          <button
                            type="button"
                            onClick={generatePassword}
                            className="text-[10px] font-mono text-[#22D3EE] hover:underline flex items-center gap-1"
                            aria-label="Generate a strong password"
                          >
                            <RefreshCw className="h-3 w-3" />
                            Generate Password
                          </button>
                        </div>
                        <div className="relative">
                          <FormControl>
                            <Input
                              type={showPassword ? "text" : "password"}
                              placeholder="••••••••"
                              autoComplete="new-password"
                              className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] pr-10 h-9 text-xs"
                              {...field}
                            />
                          </FormControl>
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#667085] hover:text-[#F5F7FA]"
                            aria-label={showPassword ? "Hide password" : "Show password"}
                          >
                            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {watchPassword && (
                    <div className="space-y-2 font-mono text-[10px]">
                      <div className="flex justify-between font-semibold">
                        <span className="text-[#9CA6B5]">Strength: {strength.label}</span>
                      </div>
                      <div className="h-1.5 w-full bg-[#111720] border border-[#202833] rounded-full overflow-hidden">
                        <div
                          className={`h-full transition-all duration-300 ${strength.color}`}
                          style={{ width: `${strength.score}%` }}
                        ></div>
                      </div>
                    </div>
                  )}

                  <FormField
                    control={form.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Confirm Password</FormLabel>
                        <div className="relative">
                          <FormControl>
                            <Input
                              type={showConfirmPassword ? "text" : "password"}
                              placeholder="••••••••"
                              autoComplete="new-password"
                              className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] pr-10 h-9 text-xs"
                              {...field}
                            />
                          </FormControl>
                          <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#667085] hover:text-[#F5F7FA]"
                            aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                          >
                            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {env.NEXT_PUBLIC_ENABLE_TURNSTILE && (
                    <div className="space-y-1">
                      <Turnstile
                        ref={turnstileRef}
                        onToken={handleToken}
                        onExpire={handleTurnstileExpire}
                        onError={handleTurnstileError}
                      />
                      {captchaError && <p className="text-xs text-[#F05252] font-mono">{captchaError}</p>}
                    </div>
                  )}

                  <FormField
                    control={form.control}
                    name="acceptTerms"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-lg border border-[#202833] p-3.5 bg-[#111720]/40">
                        <FormControl>
                          <input
                            type="checkbox"
                            id="acceptTerms"
                            checked={field.value}
                            onChange={field.onChange}
                            className="h-3.5 w-3.5 rounded border-[#202833] bg-[#090B0F] text-[#22D3EE] focus:ring-[#22D3EE] mt-1"
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <label htmlFor="acceptTerms" className="text-xs font-mono text-[#9CA6B5] leading-snug">
                            I accept the{" "}
                            <Link href="/terms" className="text-[#22D3EE] hover:underline font-bold">
                              Terms of Service
                            </Link>{" "}
                            and{" "}
                            <Link href="/privacy" className="text-[#22D3EE] hover:underline font-bold">
                              Privacy Policy
                            </Link>
                            .
                          </label>
                        </div>
                      </FormItem>
                    )}
                  />

                  <Button
                    type="submit"
                    className="w-full text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-10"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Verifying…</>
                    ) : (
                      "Register Account"
                    )}
                  </Button>
                </form>
              </Form>

              <div className="mt-5 text-center text-xs font-mono text-[#9CA6B5]">
                Already have an account?{" "}
                <Link href="/login" className="font-bold text-[#22D3EE] hover:underline">
                  Sign In
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Onboarding & Value Previews */}
        <div className="hidden lg:flex flex-1 bg-[#0D1117] border-l border-[#202833] items-center justify-center p-12 relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,#111720_0%,transparent_70%)]" />
          <div className="max-w-xl space-y-8 z-10">
            <div className="space-y-3">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md border border-[#202833] bg-[#111720] text-xs font-mono text-[#22D3EE]">
                <Activity className="h-3.5 w-3.5" />
                <span>Instant Sandbox Provisioning</span>
              </div>
              <h2 className="text-3xl font-extrabold tracking-tight text-[#F5F7FA] font-sans">
                Deploy Control Plane Instantly
              </h2>
              <p className="text-[#9CA6B5] text-sm leading-relaxed">
                Your workspace will be created instantly. Once verified, configure projects, seed domain knowledge, and authorize collaborative agent runners on your infrastructure.
              </p>
            </div>

            {/* Code snippet or flow representation */}
            <div className="border border-[#202833] bg-[#090B0F] rounded-lg p-5 font-mono text-[10px] space-y-2 text-[#9CA6B5] shadow-xl">
              <p className="text-[#22D3EE]">$ asep init workspace</p>
              <p className="text-[#667085]">{`// Checking sandbox environments...`}</p>
              <p className="text-[#2DD4A3]">✔ Active sandbox engine established</p>
              <p className="text-[#667085]">{`// Provisioning secure token vaults...`}</p>
              <p className="text-[#2DD4A3]">✔ Workspace initialized successfully</p>
            </div>
          </div>
        </div>
      </div>

      {duplicateEmailToast?.show && (
        <div className="fixed bottom-5 right-5 z-50 animate-in fade-in slide-in-from-bottom-5 duration-300">
          <div className="flex flex-col gap-3 p-4 rounded-xl border border-[#202833] bg-[#0D1117] shadow-2xl max-w-sm font-mono text-xs text-[#F5F7FA]">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded bg-[#111720] border border-[#202833] text-[#22D3EE] shrink-0">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
              <div className="flex-1 space-y-1">
                <p className="font-bold text-[#F5F7FA]">
                  This email is already registered.
                </p>
                <p className="text-[#9CA6B5]">
                  Please sign in instead. Redirecting in 2s...
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button
                size="sm"
                variant="default"
                onClick={() => router.push(`/login?email=${encodeURIComponent(duplicateEmailToast.email)}`)}
                className="text-[10px] font-bold px-3 py-1.5 h-8 bg-[#22D3EE] text-[#090B0F]"
              >
                Go to Sign In
              </Button>
            </div>
          </div>
        </div>
      )}
    </GuestRoute>
  );
}
