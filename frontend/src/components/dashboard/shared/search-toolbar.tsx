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
      <div className="relative flex-1 w-full group">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#667085] group-focus-within:text-[#22D3EE] transition-colors" />
        <Input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="pl-9 bg-[#090B0F] text-[#F5F7FA] w-full border border-[#202833] focus-visible:ring-1 focus-visible:ring-[#22D3EE]/50 focus-visible:border-[#22D3EE]/50 shadow-inner placeholder:text-[#667085] transition-all rounded-md h-10 font-mono text-sm"
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center space-x-1 pointer-events-none opacity-50 group-focus-within:opacity-100 transition-opacity">
          <kbd className="inline-flex h-5 items-center gap-1 rounded border border-[#202833] bg-[#111720] px-1.5 font-mono text-[10px] font-medium text-[#9CA6B5]">
            <span className="text-xs">⌘</span>K
          </kbd>
        </div>
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
