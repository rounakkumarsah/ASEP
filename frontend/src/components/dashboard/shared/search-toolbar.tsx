import * as React from "react";
import { Search, SlidersHorizontal, ArrowDownAZ } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface SearchToolbarProps {
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
}

export function SearchToolbar({
  placeholder = "Search...",
  value,
  onChange,
}: SearchToolbarProps) {
  return (
    <div className="flex flex-col sm:flex-row items-center gap-3 w-full bg-card p-3 rounded-lg border shadow-sm">
      <div className="relative flex-1 w-full">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="pl-9 bg-background w-full border-none shadow-none focus-visible:ring-1"
        />
      </div>

      <div className="flex items-center gap-2 w-full sm:w-auto self-end sm:self-auto">
        <Button variant="outline" size="sm" className="w-full sm:w-auto h-9">
          <SlidersHorizontal className="mr-2 h-4 w-4" />
          Filter
        </Button>
        <Button variant="outline" size="sm" className="w-full sm:w-auto h-9">
          <ArrowDownAZ className="mr-2 h-4 w-4" />
          Sort
        </Button>
      </div>
    </div>
  );
}
