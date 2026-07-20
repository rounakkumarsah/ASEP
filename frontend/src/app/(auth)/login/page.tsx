"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { Hexagon, Eye, EyeOff } from "lucide-react";
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

const loginSchema = z.object({
  username: z.string().min(3, "Username or email must be at least 3 characters"),
  password: z.string().min(6, "Password must be at least 6 characters"),
  rememberMe: z.boolean().optional(),
});

type LoginValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
      rememberMe: false,
    },
  });

  async function onSubmit(values: LoginValues) {
    setError("");
    const isMockAdmin = values.username === "admin" && values.password === "password";
    const isRegisteredUser = 
      values.username === localStorage.getItem("asep_pending_verify_email") && 
      values.password === localStorage.getItem("asep_pending_verify_password");

    if (isMockAdmin || isRegisteredUser) {
      login("mock_jwt_token_123", {
        id: "1",
        username: values.username,
        role: "supervisor",
      });
    } else {
      setError("Invalid username or password");
    }
  }

  return (
    <GuestRoute>
      <div className="flex h-screen w-full items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md border border-border/50 bg-card shadow-lg">
          <CardHeader className="text-center pb-4">
            <Link href="/" className="flex items-center justify-center space-x-2 mb-2 group">
              <Hexagon className="h-10 w-10 text-primary animate-pulse" />
              <span className="text-2xl font-bold tracking-tight">ASEP</span>
            </Link>
            <CardTitle className="text-2xl font-extrabold tracking-tight">Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access the Control Plane
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="admin or email"
                          autoComplete="email"
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
                        <FormLabel>Password</FormLabel>
                        <Link
                          href="/forgot-password"
                          className="text-xs text-primary hover:underline font-semibold"
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
                            {...field}
                          />
                        </FormControl>
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
                          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                        />
                      </FormControl>
                      <label htmlFor="rememberMe" className="text-sm font-medium text-muted-foreground select-none">
                        Remember Me
                      </label>
                    </FormItem>
                  )}
                />

                {error && (
                  <div className="text-sm text-destructive font-medium">{error}</div>
                )}

                <Button type="submit" className="w-full font-semibold">
                  Sign In
                </Button>
              </form>
            </Form>

            <div className="mt-6 text-center text-sm text-muted-foreground">
              Don&apos;t have an account?{" "}
              <Link href="/signup" className="font-semibold text-primary hover:underline">
                Get Started
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
