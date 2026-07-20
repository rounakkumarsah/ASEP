"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Hexagon, Eye, EyeOff, Check, X, RefreshCw } from "lucide-react";
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
import { Turnstile } from "@/components/auth/turnstile";
import { GuestRoute } from "@/components/auth/guest-route";

const signupSchema = z
  .object({
    firstName: z.string().min(1, "First name is required"),
    lastName: z.string().min(1, "Last name is required"),
    company: z.string().optional(),
    email: z.string().email("Invalid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string().min(8, "Confirm password must be at least 8 characters"),
    acceptTerms: z.boolean().refine((val) => val === true, {
      message: "You must accept the terms and conditions",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type SignupValues = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const router = useRouter();
  const [showPassword, setShowPassword] = React.useState(false);
  const [captchaToken, setCaptchaToken] = React.useState<string | null>(null);
  const [captchaError, setCaptchaError] = React.useState("");

  const form = useForm<SignupValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      company: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptTerms: false,
    },
  });

  const watchPassword = form.watch("password", "");

  // Password rules validation
  const rules = {
    length: watchPassword.length >= 8,
    number: /\d/.test(watchPassword),
    special: /[^A-Za-z0-9]/.test(watchPassword),
  };

  // Live password strength calculation
  const getStrength = (): { score: number; label: string; color: string } => {
    if (!watchPassword) return { score: 0, label: "None", color: "bg-muted" };
    let score = 0;
    if (watchPassword.length >= 6) score += 1;
    if (watchPassword.length >= 8) score += 1;
    if (/\d/.test(watchPassword)) score += 1;
    if (/[^A-Za-z0-9]/.test(watchPassword)) score += 1;

    switch (score) {
      case 1:
        return { score: 25, label: "Weak", color: "bg-red-500" };
      case 2:
        return { score: 50, label: "Medium", color: "bg-yellow-500" };
      case 3:
        return { score: 75, label: "Strong", color: "bg-blue-500" };
      case 4:
        return { score: 100, label: "Excellent", color: "bg-green-500" };
      default:
        return { score: 10, label: "Weak", color: "bg-red-500" };
    }
  };

  const strength = getStrength();

  // Generate strong password helper
  const generatePassword = () => {
    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+~`|}{[]:;?><,./-=";
    let newPassword = "";
    // Ensure we meet all requirements
    newPassword += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[Math.floor(Math.random() * 26)];
    newPassword += "0123456789"[Math.floor(Math.random() * 10)];
    newPassword += "!@#$%^&*()"[Math.floor(Math.random() * 10)];
    for (let i = 0; i < 9; i++) {
      newPassword += chars[Math.floor(Math.random() * chars.length)];
    }
    form.setValue("password", newPassword, { shouldValidate: true });
    form.setValue("confirmPassword", newPassword, { shouldValidate: true });
  };

  const onSubmit = (values: SignupValues) => {
    if (!captchaToken) {
      setCaptchaError("Please complete the human verification step.");
      return;
    }
    setCaptchaError("");
    // Store signup details in local storage for testing verification flow
    localStorage.setItem("asep_pending_verify_email", values.email);
    localStorage.setItem("asep_pending_verify_password", values.password);
    router.push(`/verify-email?email=${encodeURIComponent(values.email)}`);
  };

  return (
    <GuestRoute>
      <div className="flex min-h-screen w-full items-center justify-center bg-background py-12 px-4 sm:px-6 lg:px-8">
        <Card className="w-full max-w-lg border border-border/50 bg-card shadow-lg">
          <CardHeader className="text-center pb-4">
            <Link href="/" className="flex items-center justify-center space-x-2 mb-2 group">
              <Hexagon className="h-8 w-8 text-primary animate-pulse" />
              <span className="text-2xl font-bold tracking-tight">ASEP</span>
            </Link>
            <CardTitle className="text-2xl font-extrabold tracking-tight">Create your Account</CardTitle>
            <CardDescription>
              Start orchestrating autonomous local agent groups.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
                {/* Names */}
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="firstName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>First Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Jane" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="lastName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Last Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Doe" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                {/* Company & Email */}
                <FormField
                  control={form.control}
                  name="company"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Company (Optional)</FormLabel>
                      <FormControl>
                        <Input placeholder="Acme Corp" {...field} />
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
                      <FormLabel>Email Address</FormLabel>
                      <FormControl>
                        <Input type="email" placeholder="jane@company.com" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Password and generator */}
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex justify-between items-center">
                        <FormLabel>Password</FormLabel>
                        <button
                          type="button"
                          onClick={generatePassword}
                          className="text-xs text-primary hover:underline flex items-center gap-1 font-semibold"
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

                {/* Live Password Strength Meter */}
                {watchPassword && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span>Password Strength: {strength.label}</span>
                    </div>
                    <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${strength.color}`}
                        style={{ width: `${strength.score}%` }}
                      ></div>
                    </div>
                    {/* Rules */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        {rules.length ? (
                          <Check className="h-3.5 w-3.5 text-green-500" />
                        ) : (
                          <X className="h-3.5 w-3.5 text-muted-foreground/50" />
                        )}
                        <span>8+ Characters</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {rules.number ? (
                          <Check className="h-3.5 w-3.5 text-green-500" />
                        ) : (
                          <X className="h-3.5 w-3.5 text-muted-foreground/50" />
                        )}
                        <span>1+ Number</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {rules.special ? (
                          <Check className="h-3.5 w-3.5 text-green-500" />
                        ) : (
                          <X className="h-3.5 w-3.5 text-muted-foreground/50" />
                        )}
                        <span>1+ Special Char</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Confirm Password */}
                <FormField
                  control={form.control}
                  name="confirmPassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Confirm Password</FormLabel>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder="••••••••"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Turnstile */}
                <div className="space-y-1">
                  <Turnstile onVerify={(token) => setCaptchaToken(token)} />
                  {captchaError && <p className="text-xs text-destructive">{captchaError}</p>}
                </div>

                {/* Accept Terms */}
                <FormField
                  control={form.control}
                  name="acceptTerms"
                  render={({ field }) => (
                    <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border border-border/50 p-4 bg-muted/20">
                      <FormControl>
                        <input
                          type="checkbox"
                          id="acceptTerms"
                          checked={field.value}
                          onChange={field.onChange}
                          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary mt-1"
                        />
                      </FormControl>
                      <div className="space-y-1 leading-none">
                        <label htmlFor="acceptTerms" className="text-sm font-medium text-muted-foreground leading-snug">
                          I accept the terms of service and privacy policy.
                        </label>
                      </div>
                    </FormItem>
                  )}
                />

                <Button type="submit" className="w-full font-semibold">
                  Register Account
                </Button>
              </form>
            </Form>

            <div className="mt-6 text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link href="/login" className="font-semibold text-primary hover:underline">
                Sign In
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </GuestRoute>
  );
}
