"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2, Eye, EyeOff, Check, X } from "lucide-react";
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
import { GuestRoute } from "@/components/auth/guest-route";
import { Turnstile, TurnstileRef } from "@/components/auth/turnstile";
import { env } from "@/lib/config/env";

const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(12, "Password must be at least 12 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/\d/, "Password must contain at least one number")
      .regex(/[^A-Za-z0-9]/, "Password must contain at least one special character"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Confirm password does not match the entered password",
    path: ["confirmPassword"],
  });

type ResetPasswordValues = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);
  const [error, setError] = React.useState("");
  const [success, setSuccess] = React.useState(false);
  const [captchaError, setCaptchaError] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const turnstileRef = React.useRef<TurnstileRef>(null);
  const pendingValuesRef = React.useRef<ResetPasswordValues | null>(null);

  const form = useForm<ResetPasswordValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: "",
      confirmPassword: "",
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

  const onSubmit = async (values: ResetPasswordValues) => {
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
  };

  const handleToken = React.useCallback(async (freshToken: string) => {
    const values = pendingValuesRef.current;
    if (!values) {
      setIsSubmitting(false);
      turnstileRef.current?.reset();
      return;
    }

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: token,
          password: values.password,
          captchaToken: freshToken,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        setError(errorData.detail || "Unable to reset password. Token may be expired.");
        turnstileRef.current?.reset();
        setIsSubmitting(false);
        return;
      }

      setSuccess(true);
      pendingValuesRef.current = null;
      setTimeout(() => {
        router.push("/login?reset=success");
      }, 2000);
    } catch {
      setError("Unable to connect to the authentication server.");
      turnstileRef.current?.reset();
      setIsSubmitting(false);
    }
  }, [token, router]);

  const handleTurnstileError = React.useCallback(() => {
    setCaptchaError("Human verification failed. Please try again.");
    turnstileRef.current?.reset();
    setIsSubmitting(false);
  }, []);

  const handleTurnstileExpire = React.useCallback(() => {
    setCaptchaError("Verification expired. Please click Reset Password again.");
    setIsSubmitting(false);
  }, []);

  return (
    <GuestRoute>
      <div className="w-full">
        <Card className="w-full max-w-md border border-[#202833] bg-[#0D1117] shadow-xl">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-xl font-bold font-mono text-[#F5F7FA]">Reset Password</CardTitle>
            <CardDescription className="text-xs text-[#9CA6B5] font-sans">
              Set a strong, secure new password for your account.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="text-center space-y-4 py-4">
                <div className="flex justify-center">
                  <div className="p-3 bg-[#2DD4A3]/10 text-[#2DD4A3] rounded-full border border-[#2DD4A3]/20">
                    <Check className="h-6 w-6" />
                  </div>
                </div>
                <p className="text-xs font-mono text-[#2DD4A3]">
                  Password updated successfully! Redirecting to login...
                </p>
              </div>
            ) : (
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  {error && (
                    <div className="p-3 rounded border border-[#F05252]/20 bg-[#F05252]/10 text-xs font-mono text-[#F05252] text-center">
                      {error}
                    </div>
                  )}

                  {/* Password */}
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex justify-between items-center">
                          <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">New Password</FormLabel>
                          <button
                            type="button"
                            onClick={generatePassword}
                            className="text-[10px] font-mono text-[#22D3EE] hover:underline"
                          >
                            Generate Password
                          </button>
                        </div>
                        <FormControl>
                          <div className="relative">
                            <Input
                              type={showPassword ? "text" : "password"}
                              placeholder="••••••••••••"
                              autoComplete="new-password"
                              className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] pr-10"
                              {...field}
                            />
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              className="absolute inset-y-0 right-0 flex items-center pr-3 text-[#667085] hover:text-[#F5F7FA]"
                              aria-label={showPassword ? "Hide password" : "Show password"}
                            >
                              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Confirm Password */}
                  <FormField
                    control={form.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Confirm Password</FormLabel>
                        <FormControl>
                          <div className="relative">
                            <Input
                              type={showConfirmPassword ? "text" : "password"}
                              placeholder="••••••••••••"
                              autoComplete="new-password"
                              className="border-[#202833] bg-[#090B0F] text-[#F5F7FA] pr-10"
                              {...field}
                            />
                            <button
                              type="button"
                              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                              className="absolute inset-y-0 right-0 flex items-center pr-3 text-[#667085] hover:text-[#F5F7FA]"
                              aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                            >
                              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Password Strength Meter */}
                  {watchPassword && (
                    <div className="space-y-2 pt-2 font-mono text-[10px]">
                      <div className="flex justify-between items-center">
                        <span className="text-[#9CA6B5]">Strength:</span>
                        <span className="font-semibold text-[#F5F7FA]">{strength.label}</span>
                      </div>
                      <div className="h-1.5 w-full bg-[#111720] border border-[#202833] rounded-full overflow-hidden">
                        <div
                          className={`h-full ${strength.color} transition-all duration-300`}
                          style={{ width: `${strength.score}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Password Checklist */}
                  <div className="p-3 bg-[#111720]/40 border border-[#202833] rounded-lg space-y-2 text-[10px] font-mono">
                    <p className="font-semibold text-[#9CA6B5]">Requirements:</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                      <div className="flex items-center gap-2">
                        {rules.length ? <Check className="h-3.5 w-3.5 text-[#2DD4A3]" /> : <X className="h-3.5 w-3.5 text-[#667085]/50" />}
                        <span className={rules.length ? "text-[#2DD4A3]" : "text-[#667085]"}>12+ Characters</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {rules.uppercase ? <Check className="h-3.5 w-3.5 text-[#2DD4A3]" /> : <X className="h-3.5 w-3.5 text-[#667085]/50" />}
                        <span className={rules.uppercase ? "text-[#2DD4A3]" : "text-[#667085]"}>Uppercase Letter</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {rules.lowercase ? <Check className="h-3.5 w-3.5 text-[#2DD4A3]" /> : <X className="h-3.5 w-3.5 text-[#667085]/50" />}
                        <span className={rules.lowercase ? "text-[#2DD4A3]" : "text-[#667085]"}>Lowercase Letter</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {rules.number ? <Check className="h-3.5 w-3.5 text-[#2DD4A3]" /> : <X className="h-3.5 w-3.5 text-[#667085]/50" />}
                        <span className={rules.number ? "text-[#2DD4A3]" : "text-[#667085]"}>One Number</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {rules.special ? <Check className="h-3.5 w-3.5 text-[#2DD4A3]" /> : <X className="h-3.5 w-3.5 text-[#667085]/50" />}
                        <span className={rules.special ? "text-[#2DD4A3]" : "text-[#667085]"}>Special Character</span>
                      </div>
                    </div>
                  </div>

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

                  <Button
                    type="submit"
                    className="w-full text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-10 mt-4"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Resetting…</>
                    ) : (
                      "Reset Password"
                    )}
                  </Button>
                </form>
              </Form>
            )}
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
