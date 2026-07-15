import * as React from "react"
import { Search, Filter, ShieldAlert, FileKey } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export function GovernanceFilterBar() {
  return (
    <div className="flex flex-col sm:flex-row items-center gap-3 w-full bg-card p-3 rounded-lg border shadow-sm">
      <div className="relative flex-1 w-full">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input 
          type="text"
          placeholder="Search policies, agents, or resource IDs..."
          className="pl-9 bg-background w-full border-none shadow-none focus-visible:ring-1"
        />
      </div>
      
      <div className="flex items-center gap-2 w-full sm:w-auto self-end sm:self-auto overflow-x-auto pb-1 sm:pb-0">
        <Button variant="outline" size="sm" className="whitespace-nowrap h-9">
          <Filter className="mr-2 h-4 w-4" />
          Status
        </Button>
        <Button variant="outline" size="sm" className="whitespace-nowrap h-9">
          <ShieldAlert className="mr-2 h-4 w-4" />
          Risk Level
        </Button>
        <Button variant="outline" size="sm" className="whitespace-nowrap h-9">
          <FileKey className="mr-2 h-4 w-4" />
          Date Range
        </Button>
      </div>
    </div>
  )
}
