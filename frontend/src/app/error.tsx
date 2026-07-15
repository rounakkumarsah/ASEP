"use client"

import { useEffect } from "react"
import { Button } from "@/components/ui/button"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to an error reporting service in production
    console.error(error)
  }, [error])

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center space-y-4 bg-background px-4 text-center">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight text-destructive">Something went wrong!</h1>
        <p className="text-muted-foreground">An unexpected error occurred in the dashboard.</p>
      </div>
      <Button onClick={() => reset()} variant="outline">
        Try again
      </Button>
    </div>
  )
}
