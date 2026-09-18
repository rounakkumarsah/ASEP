"use client";

import * as React from "react";
import Link from "next/link";
import { 
  ChevronDown, 
  Plus, 
  Box, 
  Zap, 
  CreditCard, 
  User, 
  PanelLeft, 
  SlidersHorizontal, 
  Activity,
  SquarePen,
  History,
  Folder,
  FolderPlus,
  Check,
  X,
  ExternalLink
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";
import { useSidebarStore } from "@/lib/stores/sidebarStore";
import { useWorkspaceStore } from "@/lib/stores/workspaceStore";
import { useChatHistoryStore } from "@/lib/stores/chatHistoryStore";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/lib/providers/auth-provider";
import { apiClient } from "@/lib/api/client";

import { CreateWorkspaceModal } from "./CreateWorkspaceModal";
import { CreateProjectModal } from "./CreateProjectModal";
import { ChatHistorySheet } from "./ChatHistorySheet";

interface ProjectItem {
  id: string;
  name: string;
  slug?: string;
  description?: string | null;
}

export function TopBar() {
  const { 
    selectedProjectId, 
    selectedProjectName, 
    setSelectedProjectName, 
    setProject,
    setMessages,
    resetActiveNodes,
    setIsThinking,
    setTokenUsagePerPhase,
    addTerminalLog
  } = usePlaygroundStore();

  const {
    isMainSidebarOpen,
    toggleMainSidebar,
    isLeftPanelOpen,
    toggleLeftPanel,
    isRightPanelOpen,
    toggleRightPanel,
  } = useSidebarStore();

  const { 
    workspaces, 
    activeWorkspaceId, 
    switchWorkspace, 
    getActiveWorkspace 
  } = useWorkspaceStore();

  const {
    sessions,
    createSession,
    saveOrUpdateSession
  } = useChatHistoryStore();

  const searchParams = useSearchParams();
  const { user } = useAuth();

  // Modals & Sheets
  const [isCreateWorkspaceOpen, setIsCreateWorkspaceOpen] = React.useState(false);
  const [isCreateProjectOpen, setIsCreateProjectOpen] = React.useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = React.useState(false);

  // Projects list
  const [projects, setProjects] = React.useState<ProjectItem[]>([]);
  const [loadingProjects, setLoadingProjects] = React.useState(false);

  const activeWorkspace = getActiveWorkspace();

  // Sync project from URL query param
  React.useEffect(() => {
    const projectName = searchParams.get("projectName");
    const projectId = searchParams.get("projectId");
    if (projectName) {
      setSelectedProjectName(projectName);
      if (projectId) {
        setProject(projectId, projectName);
      }
    }
  }, [searchParams, setSelectedProjectName, setProject]);

  // Fetch projects list
  const fetchProjects = React.useCallback(async () => {
    setLoadingProjects(true);
    try {
      const res = await apiClient.get("/api/v1/projects");
      if (res.data && Array.isArray(res.data)) {
        setProjects(res.data);
      } else {
        setProjects([]);
      }
    } catch {
      // Fallback to demo projects if offline or guest
      setProjects([
        { id: "prj_default_1", name: "ASEP Web Platform", description: "Main application repository" },
        { id: "prj_default_2", name: "Agent Runtime Service", description: "LangGraph orchestration engine" },
      ]);
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  React.useEffect(() => {
    fetchProjects();
  }, [fetchProjects, activeWorkspaceId]);

  // Start a fresh conversation
  const handleNewChat = React.useCallback(() => {
    const currentMessages = usePlaygroundStore.getState().messages;

    // If current conversation is already empty (0 messages), no need to archive or create duplicate
    if (!currentMessages || currentMessages.length === 0) {
      addTerminalLog("system", "[New Chat] Current conversation is already fresh and empty. Ready for instructions.");
      return;
    }

    const currentChatId = useChatHistoryStore.getState().activeSessionId || `chat_${Date.now()}`;
    saveOrUpdateSession({
      id: currentChatId,
      messages: currentMessages,
      projectId: selectedProjectId,
      projectName: selectedProjectName,
      workspaceId: activeWorkspace.id,
      workspaceName: activeWorkspace.name,
    });

    const newSession = createSession({
      projectId: selectedProjectId,
      projectName: selectedProjectName,
      workspaceId: activeWorkspace.id,
      workspaceName: activeWorkspace.name,
    });

    setMessages([]);
    resetActiveNodes();
    setIsThinking(false);
    setTokenUsagePerPhase({});
    addTerminalLog("system", `[New Chat] Initialized fresh conversation session (${newSession.id}). Ready for instructions.`);
  }, [
    activeWorkspace.id, 
    activeWorkspace.name, 
    addTerminalLog, 
    createSession, 
    resetActiveNodes, 
    saveOrUpdateSession, 
    selectedProjectId, 
    selectedProjectName, 
    setIsThinking, 
    setMessages, 
    setTokenUsagePerPhase
  ]);

  // Keyboard shortcut listener
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + Alt + N => New Chat
      if ((e.metaKey || e.ctrlKey) && e.altKey && (e.key === "n" || e.key === "N")) {
        e.preventDefault();
        handleNewChat();
      }
      // Ctrl/Cmd + H => Toggle History (when not typing in an input)
      if ((e.metaKey || e.ctrlKey) && (e.key === "h" || e.key === "H")) {
        const target = e.target as HTMLElement;
        if (target && (target.tagName === "INPUT" || target.tagName === "TEXTAREA")) return;
        e.preventDefault();
        setIsHistoryOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleNewChat]);

  return (
    <>
      <header className="flex h-14 items-center justify-between border-b border-border/40 bg-background/95 px-3 sm:px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 min-w-0 overflow-hidden shrink-0">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1 mr-2">
          {/* Workspace & Project Switcher */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm" 
                className="gap-1.5 px-2 hover:bg-accent/50 font-medium shrink-0 max-w-[140px] sm:max-w-[200px]"
                title={`Current Workspace: ${activeWorkspace.name} (Click to switch workspace or project)`}
              >
                <div className="flex h-6 w-6 items-center justify-center rounded bg-primary/10 text-primary shrink-0">
                  <Box className="h-4 w-4" />
                </div>
                <span className="truncate text-xs sm:text-sm">{activeWorkspace.name}</span>
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="start" className="w-64 bg-[#0D1117] border border-[#202833] text-foreground p-1 shadow-2xl z-50">
              {/* Section 1: Workspaces */}
              <div className="px-2.5 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider font-mono">
                Workspaces
              </div>

              {workspaces.map((ws) => (
                <DropdownMenuItem
                  key={ws.id}
                  onClick={() => {
                    switchWorkspace(ws.id);
                    addTerminalLog("system", `[Workspace] Switched to workspace: "${ws.name}"`);
                  }}
                  className={`flex items-center justify-between px-2.5 py-1.5 text-xs rounded-md cursor-pointer ${
                    ws.id === activeWorkspaceId
                      ? "bg-primary/10 text-primary font-medium"
                      : "hover:bg-accent/50 text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <Box className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    <span className="truncate">{ws.name}</span>
                  </div>
                  {ws.id === activeWorkspaceId && <Check className="h-3.5 w-3.5 text-primary shrink-0" />}
                </DropdownMenuItem>
              ))}

              <DropdownMenuItem
                onClick={() => setIsCreateWorkspaceOpen(true)}
                className="flex items-center gap-2 px-2.5 py-1.5 text-xs text-primary hover:bg-primary/10 rounded-md cursor-pointer mt-0.5 font-medium"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Create Workspace</span>
              </DropdownMenuItem>

              <DropdownMenuSeparator className="bg-[#202833] my-1" />

              {/* Section 2: Projects in Workspace */}
              <div className="px-2.5 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider font-mono flex items-center justify-between">
                <span>Projects in Workspace</span>
                {selectedProjectName && (
                  <span className="text-primary text-[10px] lowercase font-sans">active</span>
                )}
              </div>

              <div className="max-h-40 overflow-y-auto no-scrollbar space-y-0.5">
                {projects.length === 0 ? (
                  <div className="px-2.5 py-2 text-[11px] text-muted-foreground italic">
                    {loadingProjects ? "Loading projects..." : "No projects yet in this workspace"}
                  </div>
                ) : (
                  projects.map((p) => {
                    const isCurrent = p.name === selectedProjectName;
                    return (
                      <DropdownMenuItem
                        key={p.id}
                        onClick={() => {
                          setProject(p.id, p.name);
                          addTerminalLog("system", `[Project] Switched active project to "${p.name}"`);
                        }}
                        className={`flex items-center justify-between px-2.5 py-1.5 text-xs rounded-md cursor-pointer ${
                          isCurrent
                            ? "bg-emerald-500/10 text-emerald-400 font-medium"
                            : "hover:bg-accent/50 text-foreground"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <Folder className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                          <span className="truncate">{p.name}</span>
                        </div>
                        {isCurrent && <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0" />}
                      </DropdownMenuItem>
                    );
                  })
                )}
              </div>

              {selectedProjectName && (
                <DropdownMenuItem
                  onClick={() => {
                    setProject(null, null);
                    addTerminalLog("system", "[Project] Unlinked project. Running in global workspace mode.");
                  }}
                  className="flex items-center gap-2 px-2.5 py-1.5 text-[11px] text-muted-foreground hover:text-foreground rounded-md cursor-pointer"
                >
                  <X className="h-3 w-3" />
                  <span>Unlink Current Project</span>
                </DropdownMenuItem>
              )}

              <DropdownMenuItem
                onClick={() => setIsCreateProjectOpen(true)}
                className="flex items-center gap-2 px-2.5 py-1.5 text-xs text-emerald-400 hover:bg-emerald-500/10 rounded-md cursor-pointer mt-0.5 font-medium"
              >
                <FolderPlus className="h-3.5 w-3.5" />
                <span>New Project</span>
              </DropdownMenuItem>

              <DropdownMenuSeparator className="bg-[#202833] my-1" />

              <DropdownMenuItem asChild>
                <Link
                  href="/projects"
                  className="flex items-center justify-between px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground rounded-md cursor-pointer"
                >
                  <span>Manage All Projects</span>
                  <ExternalLink className="h-3 w-3" />
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="h-4 w-px bg-border/50 shrink-0 hidden sm:block" />

          {/* New Chat Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewChat}
            className="h-8 gap-1.5 px-2.5 text-xs font-medium border-border/60 hover:bg-accent/50 shrink-0 shadow-xs text-foreground hover:text-primary transition-colors"
            title="Start fresh conversation (Ctrl+Alt+N)"
          >
            <SquarePen className="h-3.5 w-3.5 text-primary" />
            <span className="hidden sm:inline">New Chat</span>
          </Button>

          {/* Chat History Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsHistoryOpen(true)}
            className="h-8 gap-1.5 px-2.5 text-xs text-muted-foreground hover:text-foreground shrink-0 relative hover:bg-accent/50 transition-colors"
            title="Browse conversation history (Ctrl+H)"
          >
            <History className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="hidden md:inline">History</span>
            {sessions.length > 0 && (
              <Badge variant="secondary" className="px-1.5 py-0 text-[10px] font-mono h-4 ml-0.5 bg-accent/60">
                {sessions.length}
              </Badge>
            )}
          </Button>

          <div className="h-4 w-px bg-border/50 shrink-0 hidden md:block" />

          {/* Linked Project Chip */}
          <Badge 
            variant="outline" 
            onClick={() => setIsCreateProjectOpen(true)}
            className="hidden lg:inline-flex bg-primary/5 text-primary border-primary/20 hover:bg-primary/10 transition-colors whitespace-nowrap shrink-0 text-xs cursor-pointer"
            title="Click to switch or create project"
          >
            <Folder className="h-3 w-3 mr-1" />
            {selectedProjectName || "No Project Linked"}
          </Badge>

          <div className="h-4 w-px bg-border/50 hidden lg:block shrink-0" />

          {/* 3-Column Layout Toggle Controls */}
          <div className="flex items-center rounded-lg border border-border/40 bg-muted/30 p-0.5 shadow-xs shrink-0">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleMainSidebar}
                  className={cn(
                    "h-7 w-7 rounded-md transition-all",
                    isMainSidebarOpen
                      ? "bg-background text-primary shadow-xs"
                      : "text-muted-foreground hover:text-foreground opacity-60"
                  )}
                  aria-label="Toggle Main Navigation Sidebar"
                >
                  <PanelLeft className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="font-semibold text-xs">Main Sidebar (Nav)</p>
                <p className="text-[10px] text-muted-foreground">{isMainSidebarOpen ? "Click to Collapse (Ctrl+B)" : "Click to Expand (Ctrl+B)"}</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleLeftPanel}
                  className={cn(
                    "h-7 w-7 rounded-md transition-all hidden md:inline-flex",
                    isLeftPanelOpen
                      ? "bg-background text-primary shadow-xs"
                      : "text-muted-foreground hover:text-foreground opacity-60"
                  )}
                  aria-label="Toggle Configuration Panel"
                >
                  <SlidersHorizontal className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="font-semibold text-xs">Configuration Panel (Left Column)</p>
                <p className="text-[10px] text-muted-foreground">{isLeftPanelOpen ? "Click to Collapse (Ctrl+[)" : "Click to Expand (Ctrl+[)"}</p>
              </TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleRightPanel}
                  className={cn(
                    "h-7 w-7 rounded-md transition-all hidden xl:inline-flex",
                    isRightPanelOpen
                      ? "bg-background text-primary shadow-xs"
                      : "text-muted-foreground hover:text-foreground opacity-60"
                  )}
                  aria-label="Toggle Execution Trace Panel"
                >
                  <Activity className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="font-semibold text-xs">Execution Trace (Right Column)</p>
                <p className="text-[10px] text-muted-foreground">{isRightPanelOpen ? "Click to Collapse (Ctrl+])" : "Click to Expand (Ctrl+])"}</p>
              </TooltipContent>
            </Tooltip>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          <div className="hidden items-center gap-1.5 xl:flex shrink-0">
            <Badge variant="secondary" className="gap-1 font-mono text-[10px] bg-accent/30 text-muted-foreground whitespace-nowrap">
              <Zap className="h-3 w-3 text-amber-500" />
              1.2s Latency
            </Badge>
            <Badge variant="secondary" className="gap-1 font-mono text-[10px] bg-accent/30 text-muted-foreground whitespace-nowrap">
              <CreditCard className="h-3 w-3 text-emerald-500" />
              $0.02 Cost
            </Badge>
          </div>

          <div className="h-4 w-px bg-border/50 hidden xl:block shrink-0" />

          <div className="flex -space-x-2 shrink-0">
            <Avatar className="h-7 w-7 border-2 border-background">
              <AvatarFallback className="bg-primary/10 text-primary text-xs">
                {user?.first_name ? user.first_name.charAt(0).toUpperCase() : <User className="h-3 w-3" />}
              </AvatarFallback>
            </Avatar>
          </div>

          <Button size="sm" variant="outline" className="h-8 gap-1 border-dashed hidden sm:inline-flex shrink-0 text-xs">
            <Plus className="h-3.5 w-3.5" />
            Invite
          </Button>
        </div>
      </header>

      {/* Modals & Sheets */}
      <CreateWorkspaceModal
        open={isCreateWorkspaceOpen}
        onOpenChange={setIsCreateWorkspaceOpen}
        onWorkspaceCreated={(id, name) => {
          addTerminalLog("success", `[Workspace] Created and switched to new workspace: "${name}"`);
        }}
      />

      <CreateProjectModal
        open={isCreateProjectOpen}
        onOpenChange={setIsCreateProjectOpen}
        onProjectCreated={(project) => {
          addTerminalLog("success", `[Project] Created and linked project: "${project.name}"`);
          fetchProjects();
        }}
      />

      <ChatHistorySheet
        open={isHistoryOpen}
        onOpenChange={setIsHistoryOpen}
        onNewChat={handleNewChat}
      />
    </>
  );
}
