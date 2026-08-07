"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Cpu, KeyRound, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { GuestRoute } from "@/components/auth/guest-route";
import { Turnstile, TurnstileRef } from "@/components/auth/turnstile";
import { env } from "@/lib/config/env";

const forgotSchema = z.object({
  email: z.string().email("Invalid email address"),
});

type ForgotValues = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState("");
  const [captchaError, setCaptchaError] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const turnstileRef = React.useRef<TurnstileRef>(null);
  const pendingValuesRef = React.useRef<ForgotValues | null>(null);
  const form = useForm<ForgotValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: "" },
  });

  const onSubmit = async (values: ForgotValues) => {
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
      const res = await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: values.email,
          captchaToken: freshToken,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        setError(errorData.detail || "Unable to process password reset request.");
        turnstileRef.current?.reset();
        setIsSubmitting(false);
        return;
      }

      setSuccess(true);
      pendingValuesRef.current = null;
    } catch {
      setError("Unable to connect to the authentication server.");
      turnstileRef.current?.reset();
      setIsSubmitting(false);
    }
  }, []);

  const handleTurnstileError = React.useCallback(() => {
    setCaptchaError("Human verification failed. Please try again.");
    turnstileRef.current?.reset();
    setIsSubmitting(false);
  }, []);

  const handleTurnstileExpire = React.useCallback(() => {
    setCaptchaError("Verification expired. Please click Send Reset Link again.");
    setIsSubmitting(false);
  }, []);

  return (
    <GuestRoute>
      <div className="flex h-screen w-full items-center justify-center bg-[#090B0F] px-4 text-[#F5F7FA]">
        <Card className="w-full max-w-md border border-[#202833] bg-[#0D1117] shadow-xl">
          <CardHeader className="text-center pb-4">
            <Link href="/" className="flex items-center justify-center space-x-2.5 mb-4 group">
              <div className="p-1.5 rounded bg-[#111720] border border-[#202833] text-[#22D3EE] group-hover:border-[#22D3EE]/50 transition-colors">
                <Cpu className="h-5 w-5" />
              </div>
              <span className="font-mono font-bold tracking-wider text-lg text-[#F5F7FA]">ASEP</span>
            </Link>
            <div className="mx-auto h-11 w-11 rounded-md bg-[#111720] border border-[#202833] flex items-center justify-center text-[#22D3EE] mb-4">
              <KeyRound className="h-5 w-5" />
            </div>
            <CardTitle className="text-xl font-bold font-mono text-[#F5F7FA]">Forgot Password?</CardTitle>
            <CardDescription className="text-xs text-[#9CA6B5] font-sans">
              Enter your email to receive password reset instructions.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="p-3 mb-4 text-xs font-mono text-[#F05252] bg-[#F05252]/10 rounded border border-[#F05252]/20 text-center">
                {error}
              </div>
            )}
            {success ? (
              <div className="space-y-4 text-center">
                <div className="p-3 text-xs font-mono text-[#2DD4A3] bg-[#2DD4A3]/10 rounded border border-[#2DD4A3]/20">
                  Password reset link sent successfully!
                </div>
                <Link href="/login">
                  <Button variant="outline" className="w-full text-xs font-mono font-semibold border-[#202833] bg-[#111720] text-[#F5F7FA]">
                    Return to Sign In
                  </Button>
                </Link>
              </div>
            ) : (
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-mono font-semibold uppercase text-[#9CA6B5]">Email Address</FormLabel>
                        <FormControl>
                          <Input type="email" placeholder="jane@company.com" className="border-[#202833] bg-[#090B0F] text-[#F5F7FA]" {...field} />
                        </FormControl>
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
                      {captchaError && (
                        <p className="text-xs text-[#F05252] font-mono">{captchaError}</p>
                      )}
                    </div>
                  )}
                  <Button type="submit" className="w-full text-xs font-mono font-semibold bg-[#22D3EE] text-[#090B0F] hover:bg-[#67E8F9] h-10" disabled={isSubmitting}>
                    {isSubmitting ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Processing…</>
                    ) : (
                      "Send Reset Link"
                    )}
                  </Button>
                </form>
              </Form>
            )}
            {!success && (
              <div className="mt-6 text-center text-xs font-mono text-[#9CA6B5]">
                Remember your password?{" "}
                <Link href="/login" className="font-bold text-[#22D3EE] hover:underline">
                  Sign In
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
