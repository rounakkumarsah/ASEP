import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description?: string;
  isDefault?: boolean;
  createdAt: string;
}

interface WorkspaceState {
  workspaces: Workspace[];
  activeWorkspaceId: string;
  
  // Actions
  createWorkspace: (name: string, description?: string) => Workspace;
  switchWorkspace: (id: string) => void;
  deleteWorkspace: (id: string) => void;
  renameWorkspace: (id: string, newName: string) => void;
  getActiveWorkspace: () => Workspace;
}

const DEFAULT_WORKSPACE_ID = "ws_default";

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      workspaces: [
        {
          id: DEFAULT_WORKSPACE_ID,
          name: "Sachin's Workspace",
          slug: "sachins-workspace",
          description: "Primary engineering and agent workspace",
          isDefault: true,
          createdAt: new Date().toISOString(),
        },
      ],
      activeWorkspaceId: DEFAULT_WORKSPACE_ID,

      createWorkspace: (name: string, description?: string) => {
        const cleanName = name.trim();
        const slug = cleanName
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, "-")
          .replace(/^-+|-+$/g, "");
        const newWorkspace: Workspace = {
          id: `ws_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
          name: cleanName,
          slug: slug || `workspace-${Date.now()}`,
          description: description?.trim() || "",
          isDefault: false,
          createdAt: new Date().toISOString(),
        };

        set((state) => ({
          workspaces: [...state.workspaces, newWorkspace],
          activeWorkspaceId: newWorkspace.id,
        }));

        return newWorkspace;
      },

      switchWorkspace: (id: string) => {
        const exists = get().workspaces.some((w) => w.id === id);
        if (exists) {
          set({ activeWorkspaceId: id });
        }
      },

      deleteWorkspace: (id: string) => {
        const state = get();
        if (id === DEFAULT_WORKSPACE_ID || state.workspaces.length <= 1) {
          return; // Do not delete default or last workspace
        }

        const remaining = state.workspaces.filter((w) => w.id !== id);
        const nextActiveId =
          state.activeWorkspaceId === id ? remaining[0].id : state.activeWorkspaceId;

        set({
          workspaces: remaining,
          activeWorkspaceId: nextActiveId,
        });
      },

      renameWorkspace: (id: string, newName: string) => {
        const cleanName = newName.trim();
        if (!cleanName) return;

        set((state) => ({
          workspaces: state.workspaces.map((w) =>
            w.id === id ? { ...w, name: cleanName } : w
          ),
        }));
      },

      getActiveWorkspace: () => {
        const state = get();
        const found = state.workspaces.find((w) => w.id === state.activeWorkspaceId);
        return found || state.workspaces[0];
      },
    }),
    {
      name: "asep_workspaces_storage_v1",
    }
  )
);
