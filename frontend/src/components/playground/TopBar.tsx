"use client";

import * as React from "react";
import { ChevronDown, Plus, Box, Zap, CreditCard, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import { useSearchParams } from "next/navigation";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/lib/providers/auth-provider";

export function TopBar() {
  const { selectedProjectName, setSelectedProjectName } = usePlaygroundStore();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  
  React.useEffect(() => {
    const projectName = searchParams.get("projectName");
    if (projectName) {
      setSelectedProjectName(projectName);
    }
  }, [searchParams, setSelectedProjectName]);

  const orgName = user?.first_name ? `${user.first_name}'s Workspace` : "Personal Workspace";

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/40 bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center gap-4">
        {/* Org Switcher */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2 px-2 hover:bg-accent/50 font-medium">
              <div className="flex h-6 w-6 items-center justify-center rounded bg-primary/10 text-primary">
                <Box className="h-4 w-4" />
              </div>
              {orgName}
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-48">
            <DropdownMenuItem>{orgName}</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="h-4 w-px bg-border/50" />

        <span className="text-sm font-semibold tracking-tight text-foreground/90">
          Engineering Workspace
        </span>

        <Badge variant="outline" className="hidden sm:inline-flex bg-primary/5 text-primary border-primary/20 hover:bg-primary/10 transition-colors">
          {selectedProjectName || "No Project Linked"}
        </Badge>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-1.5 md:flex">
          <Badge variant="secondary" className="gap-1 font-mono text-[10px] bg-accent/30 text-muted-foreground">
            <Zap className="h-3 w-3 text-amber-500" />
            1.2s Latency
          </Badge>
          <Badge variant="secondary" className="gap-1 font-mono text-[10px] bg-accent/30 text-muted-foreground">
            <CreditCard className="h-3 w-3 text-emerald-500" />
            $0.02 Cost
          </Badge>
        </div>

        <div className="h-4 w-px bg-border/50 hidden md:block" />

        <div className="flex -space-x-2">
          <Avatar className="h-7 w-7 border-2 border-background">
            <AvatarFallback className="bg-primary/10 text-primary text-xs">
              {user?.first_name ? user.first_name.charAt(0).toUpperCase() : <User className="h-3 w-3" />}
            </AvatarFallback>
          </Avatar>
        </div>

        <Button size="sm" variant="outline" className="h-8 gap-1 border-dashed">
          <Plus className="h-3.5 w-3.5" />
          Invite
        </Button>
      </div>
    </header>
  );
}
