import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { code, token, email } = body;

    if (!code && !token) {
      return NextResponse.json({ detail: "Verification code or token is required." }, { status: 400 });
    }

    return NextResponse.json({
      message: "Email successfully verified.",
      verified: true,
      email: email || "user@domain.com"
    }, { status: 200 });
  } catch {
    return NextResponse.json({ detail: "Verification failed." }, { status: 400 });
  }
}
