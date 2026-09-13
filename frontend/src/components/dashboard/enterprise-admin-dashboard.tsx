"use client";

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { Activity, Cpu, DollarSign, Users } from "lucide-react";

// --- Mock Data Generators ---
const mockTokenUsageData = [
  { role: "Admin", tokens: 1250000 },
  { role: "Operator", tokens: 3450000 },
  { role: "Standard", tokens: 850000 },
];

const mockExecutionTimeData = [
  { day: "Mon", executionHours: 12 },
  { day: "Tue", executionHours: 18 },
  { day: "Wed", executionHours: 15 },
  { day: "Thu", executionHours: 24 },
  { day: "Fri", executionHours: 20 },
  { day: "Sat", executionHours: 8 },
  { day: "Sun", executionHours: 10 },
];

const mockModelUsageData = [
  { name: "OpenAI (GPT-4)", value: 65 },
  { name: "Local Ollama (Llama 3)", value: 35 },
];

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"];

export function EnterpriseAdminDashboard() {
  const [isMounted, setIsMounted] = useState(false);
  const [tokenCost, setTokenCost] = useState(0);

  useEffect(() => {
    setIsMounted(true);
    // Simulate fetching cost based on tokens
    const totalTokens = mockTokenUsageData.reduce((acc, curr) => acc + curr.tokens, 0);
    // Rough estimate: $0.01 per 1K tokens for blended usage
    setTokenCost((totalTokens / 1000) * 0.01);
  }, []);

  if (!isMounted) return null; // Avoid hydration mismatch

  return (
    <div className="flex flex-col gap-6 p-8 w-full max-w-7xl mx-auto bg-background/50">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Enterprise Dashboard</h2>
        <p className="text-muted-foreground">
          Monitor your platform&apos;s AI usage, agent execution metrics, and operational costs.
        </p>
      </div>

      {/* Overview Metric Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Estimated Monthly API Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${tokenCost.toFixed(2)}</div>
            <p className="text-xs text-muted-foreground">
              +12.5% from last month
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tokens Processed</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(mockTokenUsageData.reduce((a, b) => a + b.tokens, 0) / 1000000).toFixed(2)}M
            </div>
            <p className="text-xs text-muted-foreground">
              Tokens consumed across all roles
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">142</div>
            <p className="text-xs text-muted-foreground">
              Currently running in background
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">573</div>
            <p className="text-xs text-muted-foreground">
              +48 new users this week
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Token Usage Bar Chart */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Token Usage by RBAC Role</CardTitle>
            <CardDescription>
              Millions of tokens consumed per role this month.
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mockTokenUsageData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                <XAxis 
                  dataKey="role" 
                  stroke="#888888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#888888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(value) => `${value / 1000000}M`} 
                />
                <RechartsTooltip 
                  cursor={{ fill: 'transparent' }} 
                  contentStyle={{ borderRadius: '8px', backgroundColor: 'var(--background)', border: '1px solid var(--border)' }}
                />
                <Bar dataKey="tokens" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Model Breakdown Donut Chart */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Model Usage Breakdown</CardTitle>
            <CardDescription>
              Cloud vs. Local LLM execution share.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center items-center h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={mockModelUsageData}
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {mockModelUsageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ borderRadius: '8px', backgroundColor: 'var(--background)', border: '1px solid var(--border)' }}
                />
                <Legend verticalAlign="bottom" height={36}/>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Agent Execution Line Chart */}
        <Card className="col-span-7">
          <CardHeader>
            <CardTitle>Active Agent Execution Time</CardTitle>
            <CardDescription>
              Total hours of autonomous agent execution over the last 7 days.
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockExecutionTimeData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                <XAxis 
                  dataKey="day" 
                  stroke="#888888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#888888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  tickFormatter={(value) => `${value}h`} 
                />
                <RechartsTooltip 
                  contentStyle={{ borderRadius: '8px', backgroundColor: 'var(--background)', border: '1px solid var(--border)' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="executionHours" 
                  stroke="#10b981" 
                  strokeWidth={3} 
                  dot={{ r: 4, fill: '#10b981', strokeWidth: 0 }} 
                  activeDot={{ r: 6 }} 
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
