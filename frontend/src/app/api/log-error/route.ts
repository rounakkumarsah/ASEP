import { NextResponse } from 'next/server';
import * as fs from 'fs';
import * as path from 'path';

export async function POST(req: Request) {
  try {
    const data = await req.json();
    console.log("=== FRONTEND ERROR RECEIVED ===");
    console.log(data);
    
    // Also write to a file in /tmp so I can read it
    const logPath = path.join(process.cwd(), 'frontend_error.log');
    fs.appendFileSync(logPath, JSON.stringify(data, null, 2) + "\n\n");
    
    return NextResponse.json({ success: true });
  } catch (err) {
    return NextResponse.json({ success: false, error: String(err) });
  }
}
