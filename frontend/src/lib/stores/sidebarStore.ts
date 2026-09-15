"use client";

import { create } from "zustand";

interface SidebarState {
  // Column 1: Global Main Navigation Sidebar (Far Left)
  isMainSidebarOpen: boolean;
  toggleMainSidebar: () => void;
  setMainSidebarOpen: (open: boolean) => void;

  // Column 2: Playground Configuration Panel (Left Column)
  isLeftPanelOpen: boolean;
  toggleLeftPanel: () => void;
  setLeftPanelOpen: (open: boolean) => void;

  // Column 3: Playground Execution Trace Panel (Right Column)
  isRightPanelOpen: boolean;
  toggleRightPanel: () => void;
  setRightPanelOpen: (open: boolean) => void;

  // Reset all to default open
  resetPanels: () => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  // Defaults: all open on desktop for complete workspace experience
  isMainSidebarOpen: true,
  toggleMainSidebar: () =>
    set((state) => {
      const next = !state.isMainSidebarOpen;
      if (typeof window !== "undefined") {
        try {
          localStorage.setItem("asep_main_sidebar_open", JSON.stringify(next));
        } catch {}
      }
      return { isMainSidebarOpen: next };
    }),
  setMainSidebarOpen: (open: boolean) => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("asep_main_sidebar_open", JSON.stringify(open));
      } catch {}
    }
    set({ isMainSidebarOpen: open });
  },

  isLeftPanelOpen: true,
  toggleLeftPanel: () =>
    set((state) => {
      const next = !state.isLeftPanelOpen;
      if (typeof window !== "undefined") {
        try {
          localStorage.setItem("asep_left_panel_open", JSON.stringify(next));
        } catch {}
      }
      return { isLeftPanelOpen: next };
    }),
  setLeftPanelOpen: (open: boolean) => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("asep_left_panel_open", JSON.stringify(open));
      } catch {}
    }
    set({ isLeftPanelOpen: open });
  },

  isRightPanelOpen: true,
  toggleRightPanel: () =>
    set((state) => {
      const next = !state.isRightPanelOpen;
      if (typeof window !== "undefined") {
        try {
          localStorage.setItem("asep_right_panel_open", JSON.stringify(next));
        } catch {}
      }
      return { isRightPanelOpen: next };
    }),
  setRightPanelOpen: (open: boolean) => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("asep_right_panel_open", JSON.stringify(open));
      } catch {}
    }
    set({ isRightPanelOpen: open });
  },

  resetPanels: () =>
    set({
      isMainSidebarOpen: true,
      isLeftPanelOpen: true,
      isRightPanelOpen: true,
    }),
}));
