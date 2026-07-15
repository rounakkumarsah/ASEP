import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center space-y-4 bg-background px-4 text-center">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">404</h1>
        <p className="text-muted-foreground">The page you are looking for does not exist.</p>
      </div>
      <Link href="/">
        <Button variant="default">Return to Dashboard</Button>
      </Link>
    </div>
  )
}
