"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global Error Caught:", error);
    // Send to our debug endpoint
    fetch('/api/log-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: error.message,
        stack: error.stack,
        digest: error.digest,
        url: window.location.href,
        type: "GLOBAL_ERROR"
      })
    }).catch(e => console.error("Failed to log error:", e));
  }, [error]);

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center space-y-4 bg-[#090B0F] px-4 text-center font-mono">
      <div className="space-y-2 max-w-2xl w-full text-left">
        <h1 className="text-2xl font-bold tracking-tight text-red-500">
          Global App Error!
        </h1>
        <p className="text-muted-foreground text-sm">
          Something went terribly wrong. Here is the exact crash details:
        </p>
        <div className="bg-black/50 border border-red-500/30 rounded p-4 overflow-auto max-h-[50vh] text-left">
          <p className="text-red-400 font-bold mb-2">{error.name}: {error.message}</p>
          <pre className="text-xs text-gray-400 whitespace-pre-wrap">{error.stack}</pre>
        </div>
      </div>
      <Button onClick={() => reset()} variant="outline" className="mt-4">
        Try again
      </Button>
    </div>
  );
}
