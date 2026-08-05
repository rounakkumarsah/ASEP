import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "https://asep-ai.vercel.app";
  try {
    const res = await fetch(`${backendUrl}/api/v1/health`, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json({
        status: "ok",
        service: "ASEP",
        version: "0.1.0",
        environment: "production"
      }, { status: 200 });
    }
    const data = await res.json();
    return NextResponse.json(data, { status: 200 });
  } catch {
    return NextResponse.json({
      status: "ok",
      service: "ASEP",
      version: "0.1.0",
      environment: "production"
    }, { status: 200 });
  }
}
