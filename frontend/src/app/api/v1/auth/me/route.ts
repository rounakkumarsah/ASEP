import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    id: "usr_active_session",
    email: "user@domain.com",
    username: "user",
    first_name: "Active",
    last_name: "User",
    role: "user",
    email_verified: true,
  }, { status: 200 });
}
