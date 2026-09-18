"use client";

import * as React from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  History, 
  Search, 
  Plus, 
  Trash2, 
  MessageSquare, 
  Clock, 
  Folder, 
  Check, 
  Edit2, 
  X
} from "lucide-react";
import { useChatHistoryStore, ChatSession } from "@/lib/stores/chatHistoryStore";
import { usePlaygroundStore } from "@/lib/stores/playgroundStore";

interface ChatHistorySheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onNewChat: () => void;
}

function formatRelativeTime(dateString: string): string {
  try {
    const diffMs = Date.now() - new Date(dateString).getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return "Just now";
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour}h ago`;
    const diffDay = Math.floor(diffHour / 24);
    if (diffDay === 1) return "Yesterday";
    if (diffDay < 7) return `${diffDay}d ago`;
    return new Date(dateString).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  } catch {
    return "Recently";
  }
}

export function ChatHistorySheet({ open, onOpenChange, onNewChat }: ChatHistorySheetProps) {
  const [search, setSearch] = React.useState("");
  const [selectedProjectFilter, setSelectedProjectFilter] = React.useState<string>("all");
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [editTitle, setEditTitle] = React.useState("");

  const { sessions, activeSessionId, setActiveSessionId, deleteSession, renameSession, clearAllSessions } = useChatHistoryStore();
  const { setMessages, setProject, addTerminalLog } = usePlaygroundStore();

  // Extract unique projects from sessions for filtering
  const availableProjects = React.useMemo(() => {
    const map = new Map<string, string>();
    sessions.forEach((s) => {
      if (s.projectId && s.projectName) {
        map.set(s.projectId, s.projectName);
      }
    });
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }));
  }, [sessions]);

  // Filter sessions
  const filteredSessions = React.useMemo(() => {
    return sessions.filter((s) => {
      const matchesSearch =
        !search.trim() ||
        s.title.toLowerCase().includes(search.toLowerCase()) ||
        s.lastMessageSnippet.toLowerCase().includes(search.toLowerCase());

      const matchesProject =
        selectedProjectFilter === "all" ||
        (selectedProjectFilter === "none" && !s.projectId) ||
        s.projectId === selectedProjectFilter;

      return matchesSearch && matchesProject;
    });
  }, [sessions, search, selectedProjectFilter]);

  const handleSelectSession = (session: ChatSession) => {
    setActiveSessionId(session.id);
    setMessages(session.messages || []);
    if (session.projectId) {
      setProject(session.projectId, session.projectName);
    }
    addTerminalLog("system", `[Chat Session] Switched to conversation: "${session.title}" (${session.messages.length} messages)`);
    onOpenChange(false);
  };

  const handleStartRename = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingId(session.id);
    setEditTitle(session.title);
  };

  const handleSaveRename = (e: React.MouseEvent | React.FormEvent, id: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (editTitle.trim()) {
      renameSession(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm("Delete this conversation from history?")) {
      deleteSession(id);
    }
  };

  const handleClearAll = () => {
    if (confirm("Are you sure you want to delete all chat history? This cannot be undone.")) {
      clearAllSessions();
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md bg-[#0D1117] border-l border-[#202833] text-foreground p-0 flex flex-col shadow-2xl z-50"
      >
        <SheetHeader className="p-4 border-b border-[#202833] flex flex-row items-center justify-between space-y-0 shrink-0">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <History className="h-4 w-4" />
            </div>
            <div>
              <SheetTitle className="text-sm font-semibold text-[#F5F7FA]">Chat History</SheetTitle>
              <SheetDescription className="text-[11px] text-muted-foreground">
                {sessions.length} conversation{sessions.length === 1 ? "" : "s"} saved
              </SheetDescription>
            </div>
          </div>
          <Button
            size="sm"
            onClick={() => {
              onNewChat();
              onOpenChange(false);
            }}
            className="h-8 text-xs font-semibold bg-primary hover:bg-primary/90 text-primary-foreground gap-1.5 shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            New Chat
          </Button>
        </SheetHeader>

        {/* Search & Project Filters */}
        <div className="p-3 border-b border-[#202833] space-y-2 shrink-0 bg-[#090B0F]/50">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search conversations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8 pr-8 h-8 text-xs bg-[#111720] border-[#202833] focus-visible:ring-primary"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          {availableProjects.length > 0 && (
            <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-0.5 text-[11px]">
              <button
                onClick={() => setSelectedProjectFilter("all")}
                className={`px-2 py-0.5 rounded-full whitespace-nowrap transition-colors ${
                  selectedProjectFilter === "all"
                    ? "bg-primary/20 text-primary font-medium"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                All Projects
              </button>
              {availableProjects.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedProjectFilter(p.id)}
                  className={`px-2 py-0.5 rounded-full whitespace-nowrap flex items-center gap-1 transition-colors ${
                    selectedProjectFilter === p.id
                      ? "bg-primary/20 text-primary font-medium"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Folder className="h-3 w-3" />
                  {p.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2 min-h-0">
          {filteredSessions.length === 0 ? (
            <div className="h-48 flex flex-col items-center justify-center text-center p-4">
              <div className="h-10 w-10 rounded-xl bg-muted/20 flex items-center justify-center text-muted-foreground mb-2">
                <MessageSquare className="h-5 w-5" />
              </div>
              <p className="text-xs font-semibold text-[#F5F7FA]">
                {search ? "No conversations match your search" : "No chat history yet"}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1 max-w-xs">
                {search
                  ? "Try searching for a different keyword or clear the filter."
                  : "Start chatting in the playground to automatically build your conversation history."}
              </p>
            </div>
          ) : (
            filteredSessions.map((session) => {
              const isActive = session.id === activeSessionId;
              const isEditing = session.id === editingId;

              return (
                <div
                  key={session.id}
                  onClick={() => handleSelectSession(session)}
                  className={`group relative rounded-xl border p-3 cursor-pointer transition-all ${
                    isActive
                      ? "bg-primary/5 border-primary/40 shadow-sm"
                      : "bg-[#111720]/60 hover:bg-[#111720] border-[#202833] hover:border-[#2A3441]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    {isEditing ? (
                      <form
                        onSubmit={(e) => handleSaveRename(e, session.id)}
                        className="flex-1 flex items-center gap-1.5"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Input
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          className="h-7 text-xs bg-[#0D1117] border-[#202833]"
                          autoFocus
                        />
                        <Button
                          type="submit"
                          size="icon"
                          className="h-7 w-7 bg-primary text-primary-foreground shrink-0"
                        >
                          <Check className="h-3 w-3" />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => setEditingId(null)}
                          className="h-7 w-7 text-muted-foreground shrink-0"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </form>
                    ) : (
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          {isActive && <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />}
                          <h4 className="text-xs font-semibold text-[#F5F7FA] truncate group-hover:text-primary transition-colors">
                            {session.title}
                          </h4>
                        </div>
                        <p className="text-[11px] text-muted-foreground/80 truncate mt-1 line-clamp-1">
                          {session.lastMessageSnippet}
                        </p>
                      </div>
                    )}

                    {!isEditing && (
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                        <button
                          type="button"
                          onClick={(e) => handleStartRename(e, session)}
                          className="p-1 rounded hover:bg-accent text-muted-foreground hover:text-foreground"
                          title="Rename chat"
                        >
                          <Edit2 className="h-3 w-3" />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleDelete(e, session.id)}
                          className="p-1 rounded hover:bg-destructive/20 text-muted-foreground hover:text-destructive"
                          title="Delete chat"
                        >
                          <Trash2 className="h-3 w-3" />
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Metadata footer */}
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#202833]/60 text-[10px] text-muted-foreground font-mono">
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-3 w-3" />
                      <span>{formatRelativeTime(session.updatedAt || session.createdAt)}</span>
                      <span>•</span>
                      <span>{session.messageCount} msg{session.messageCount === 1 ? "" : "s"}</span>
                    </div>

                    {session.projectName ? (
                      <Badge variant="outline" className="text-[10px] py-0 px-1.5 border-primary/20 bg-primary/5 text-primary">
                        <Folder className="h-2.5 w-2.5 mr-1" />
                        {session.projectName}
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground/60 text-[10px]">No project</span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        {sessions.length > 0 && (
          <div className="p-3 border-t border-[#202833] flex items-center justify-between text-xs text-muted-foreground shrink-0 bg-[#090B0F]">
            <span>{sessions.length} conversation{sessions.length === 1 ? "" : "s"}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearAll}
              className="h-7 text-[11px] text-muted-foreground hover:text-destructive gap-1 px-2"
            >
              <Trash2 className="h-3 w-3" />
              Clear All
            </Button>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
