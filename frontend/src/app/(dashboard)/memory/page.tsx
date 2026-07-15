export default function MemoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Memory</h1>
        <p className="text-muted-foreground">Manage long-term agent memory and context.</p>
      </div>
      <div className="h-[400px] w-full rounded-md border border-dashed flex items-center justify-center text-muted-foreground">
        Memory Content Placeholder
      </div>
    </div>
  )
}
