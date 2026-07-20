import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Hexagon } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center space-y-6 bg-background px-4 text-center">
      <div className="flex items-center space-x-2 mb-2">
        <Hexagon className="h-10 w-10 text-primary animate-pulse" />
        <span className="text-3xl font-extrabold tracking-tight">ASEP</span>
      </div>
      <div className="space-y-3 max-w-md">
        <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
          404 - Not Found
        </h1>
        <p className="text-muted-foreground leading-relaxed">
          The autonomous route you requested is unavailable or has been archived. Check the URL or return to the main landing page.
        </p>
      </div>
      <Link href="/">
        <Button variant="default" className="font-semibold shadow-md">
          Return to Safety
        </Button>
      </Link>
    </div>
  );
}
