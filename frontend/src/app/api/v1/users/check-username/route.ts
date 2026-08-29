import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const rawUsername = searchParams.get("username");

  if (!rawUsername) {
    return NextResponse.json({ detail: "Username parameter is required" }, { status: 400 });
  }

  const username = rawUsername.trim().toLowerCase();

  // Validate formatting constraints
  if (username.length < 3 || username.length > 30) {
    return NextResponse.json({
      available: false,
      suggestions: [`${username}1`, `${username}_dev`],
      message: "Username must be between 3 and 30 characters"
    }, { status: 200 });
  }

  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    return NextResponse.json({
      available: false,
      suggestions: [],
      message: "Letters, numbers, and underscores only"
    }, { status: 200 });
  }

  // Check against backend if available
  const backendUrl = process.env.BACKEND_API_URL;
  if (backendUrl) {
    try {
      const res = await fetch(`${backendUrl}/api/v1/users/check-username?username=${encodeURIComponent(username)}`, {
        cache: "no-store",
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data, { status: 200 });
      }
    } catch {
      // Fallback to local serverless validation
    }
  }

  // System reserved and registered usernames
  const SYSTEM_RESERVED = new Set([
    "admin",
    "administrator",
    "root",
    "system",
    "superuser",
    "support",
    "security",
    "api",
    "billing",
    "operator",
    "auth",
    "moderator"
  ]);

  if (SYSTEM_RESERVED.has(username)) {
    return NextResponse.json({
      available: false,
      suggestions: [
        `${username}_dev`,
        `${username}_ai`,
        `${username}99`,
        `the_${username}`
      ],
      message: "Username is reserved by system policy"
    }, { status: 200 });
  }

  return NextResponse.json({
    available: true,
    suggestions: [],
    message: "Username is available"
  }, { status: 200 });
}
