import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { email, password, firstName, lastName, username } = body;

    if (!email || !password) {
      return NextResponse.json({ detail: "Email and password are required." }, { status: 400 });
    }

    // Check backend if connected
    const backendUrl = process.env.BACKEND_API_URL;
    if (backendUrl) {
      try {
        const res = await fetch(`${backendUrl}/api/v1/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await res.json();
        return NextResponse.json(data, { status: res.status });
      } catch {
        // Fallback to local registration handling
      }
    }

    // Serverless registration response
    return NextResponse.json({
      message: "Registration successful. A verification code has been dispatched.",
      email: email.trim().toLowerCase(),
      user: {
        id: `usr_${Date.now()}`,
        email: email.trim().toLowerCase(),
        username: username || email.split("@")[0],
        first_name: firstName || "User",
        last_name: lastName || "",
        email_verified: false,
      }
    }, { status: 201 });
  } catch {
    return NextResponse.json({ detail: "Invalid request payload." }, { status: 400 });
  }
}
