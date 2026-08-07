"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Cpu, Eye, EyeOff, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/providers/auth-provider";
import { GuestRoute } from "@/components/auth/guest-route";
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
import { env } from "@/lib/config/env";

const loginSchema = z.object({
  username: z.string().min(3, "Username or email must be at least 3 characters"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});

type LoginValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const searchParams = useSearchParams();
  const emailParam = searchParams.get("email");

  const [error, setError] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [captchaError, setCaptchaError] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const turnstileRef = React.useRef<TurnstileRef>(null);
  const pendingValuesRef = React.useRef<LoginValues | null>(null);
  const passwordRef = React.useRef<HTMLInputElement | null>(null);
  const [oauthLoading, setOauthLoading] = React.useState(false);

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

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: emailParam || "",
      password: "",
      rememberMe: false,
    },
  });

  React.useEffect(() => {
    if (emailParam) {
      form.setValue("username", emailParam, { shouldValidate: true });
      setTimeout(() => {
        passwordRef.current?.focus();
      }, 150);
    }
  }, [emailParam, form]);

  async function onSubmit(values: LoginValues) {
    if (isSubmitting) return;
    setError("");
    setCaptchaError("");

    pendingValuesRef.current = values;
    setIsSubmitting(true);

    if (!env.NEXT_PUBLIC_ENABLE_TURNSTILE) {
      handleToken("mock-turnstile-token");
      return;
    }

    turnstileRef.current?.execute();
  }

  const handleToken = React.useCallback(async (freshToken: string) => {
    const values = pendingValuesRef.current;
    if (!values) {
      setIsSubmitting(false);
      turnstileRef.current?.reset();
      return;
    }

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: values.username,
          password: values.password,
          rememberMe: values.rememberMe,
          captchaToken: freshToken,
        }),
        credentials: "include",
      });

      if (!res.ok) {
        const errorData = await res.json();
        setError(errorData.detail || "Invalid email or password");
        turnstileRef.current?.reset();
        setIsSubmitting(false);
        return;
      }

      const tokenData = await res.json();

      const userRes = await fetch(`${API_URL}/api/v1/auth/me`, {
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      if (!userRes.ok) {
        setError("Failed to fetch user profile after login.");
        turnstileRef.current?.reset();
        setIsSubmitting(false);
        return;
      }

      const userData = await userRes.json();
      pendingValuesRef.current = null;
      login(tokenData.access_token, userData);
    } catch {
      setError("Unable to connect to the authentication server.");
      turnstileRef.current?.reset();
      setIsSubmitting(false);
    }
  }, [login]);

  const handleTurnstileError = React.useCallback(() => {
    setCaptchaError("Human verification failed. Please try again.");
    turnstileRef.current?.reset();
    setIsSubmitting(false);
  }, []);

  const handleTurnstileExpire = React.useCallback(() => {
    setCaptchaError("Verification expired. Please click Sign In again.");
    setIsSubmitting(false);
  }, []);

  return (
    <GuestRoute>
      <div className="flex h-screen w-full items-center justify-center bg-[#090B0F] px-4 text-[#F5F7FA]">
        <Card className="w-full max-w-md border border-[#202833] bg-[#0D1117] shadow-xl">
          <CardHeader className="text-center pb-4">
            <Link href="/" className="flex items-center justify-center space-x-2.5 mb-2 group">
              <div className="p-1.5 rounded bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/50 transition-colors">
                <Cpu className="h-5 w-5" />
              </div>
              <span className="font-mono font-bold tracking-wider text-lg text-[#F5F7FA]">ASEP</span>
            </Link>
            <CardTitle className="text-xl font-bold font-mono text-[#F5F7FA]">Sign In</CardTitle>
            <CardDescription className="text-xs text-[#9CA6B5] font-sans">
              Enter your credentials to access the Control Plane
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 mb-6">
              <button
                type="button"
                id="github-oauth-btn"
                onClick={handleGithubLogin}
                disabled={oauthLoading}
                className="w-full flex items-center justify-center gap-3 px-4 py-2 rounded border border-[#202833] bg-[#111720] hover:bg-[#111720]/80 transition-all text-xs font-mono text-[#F5F7FA] disabled:opacity-60 h-10"
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
                className="w-full flex items-center justify-center gap-3 px-4 py-2 rounded border border-[#202833] bg-[#111720] hover:bg-[#111720]/80 transition-all text-xs font-mono text-[#F5F7FA] disabled:opacity-60 h-10"
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
            
            <div className="relative my-5">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-[#202833]" />
              </div>
              <div className="relative flex justify-center text-[10px] uppercase font-mono">
                <span className="bg-[#0D1117] px-2 text-[#667085]">or continue with email</span>
              </div>
            </div>

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Email or Username</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="admin or email"
                          autoComplete="email"
                          className="border-[#202833] bg-[#090B0F] text-[#F5F7FA]"
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
                        <Link
                          href="/forgot-password"
                          className="text-[10px] font-mono text-[#22D3EE] hover:underline"
                        >
                          Forgot Password?
                        </Link>
                      </div>
                      <div className="relative">
                        <FormControl>
                          <Input
                            type={showPassword ? "text" : "password"}
                            placeholder="••••••"
                            autoComplete="current-password"
                            className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] pr-10"
                            {...field}
                            ref={(e) => {
                              field.ref(e);
                              passwordRef.current = e;
                            }}
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

                {/* Remember Me */}
                <FormField
                  control={form.control}
                  name="rememberMe"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <input
                          type="checkbox"
                          id="rememberMe"
                          checked={field.value}
                          onChange={field.onChange}
                          className="h-3.5 w-3.5 rounded border-[#202833] bg-[#090B0F] text-[#22D3EE] focus:ring-[#22D3EE]"
                        />
                      </FormControl>
                      <label htmlFor="rememberMe" className="text-xs font-mono text-[#9CA6B5] select-none">
                        Remember Me
                      </label>
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
                    {captchaError && (
                      <p className="text-xs text-[#F05252] font-mono">{captchaError}</p>
                    )}
                  </div>
                )}

                {error && (
                  <div className="text-xs font-mono text-[#F05252] bg-[#F05252]/10 rounded border border-[#F05252]/20 p-2 text-center">{error}</div>
                )}

                <Button
                  type="submit"
                  className="w-full text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-10"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Verifying…</>
                  ) : (
                    "Sign In"
                  )}
                </Button>
              </form>
            </Form>

            <div className="mt-6 text-center text-xs font-mono text-[#9CA6B5]">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="font-bold text-[#22D3EE] hover:underline">
                Get Started
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
