"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Hexagon, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { GuestRoute } from "@/components/auth/guest-route";

const forgotSchema = z.object({
  email: z.string().email("Invalid email address"),
});

type ForgotValues = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [success, setSuccess] = React.useState(false);
  const form = useForm<ForgotValues>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: "" },
  });

  const onSubmit = () => {
    setSuccess(true);
  };

  return (
    <GuestRoute>
      <div className="flex h-screen w-full items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md border border-border/50 bg-card shadow-lg">
          <CardHeader className="text-center pb-4">
            <Link href="/" className="flex items-center justify-center space-x-2 mb-4">
              <Hexagon className="h-10 w-10 text-primary animate-pulse" />
              <span className="text-2xl font-bold tracking-tight">ASEP</span>
            </Link>
            <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary mb-4">
              <KeyRound className="h-6 w-6" />
            </div>
            <CardTitle className="text-2xl font-bold">Forgot Password?</CardTitle>
            <CardDescription>
              Enter your email and we&apos;ll send you instructions to reset your password.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="space-y-4 text-center">
                <div className="p-3 text-sm text-green-600 bg-green-500/10 rounded-lg border border-green-500/20 font-semibold">
                  Password reset link sent successfully! Check your inbox.
                </div>
                <Link href="/login">
                  <Button variant="outline" className="w-full font-semibold">
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
                        <FormLabel>Email Address</FormLabel>
                        <FormControl>
                          <Input type="email" placeholder="jane@company.com" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <Button type="submit" className="w-full font-semibold">
                    Send Reset Link
                  </Button>
                </form>
              </Form>
            )}
            {!success && (
              <div className="mt-6 text-center text-sm text-muted-foreground">
                Remember your password?{" "}
                <Link href="/login" className="font-semibold text-primary hover:underline">
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
