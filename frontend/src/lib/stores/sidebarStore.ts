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

const getInitialMainSidebar = (): boolean => {
  if (typeof window !== "undefined") {
    try {
      const initialized = localStorage.getItem("asep_sidebar_v2_initialized");
      if (!initialized) {
        localStorage.setItem("asep_sidebar_v2_initialized", "true");
        localStorage.setItem("asep_main_sidebar_open", "false");
        return false;
      }
      const stored = localStorage.getItem("asep_main_sidebar_open");
      if (stored !== null) return JSON.parse(stored);
    } catch {}
  }
  return false;
};

const getStoredBoolean = (key: string, fallback: boolean): boolean => {
  if (typeof window !== "undefined") {
    try {
      const item = localStorage.getItem(key);
      if (item !== null) return JSON.parse(item);
    } catch {}
  }
  return fallback;
};

export const useSidebarStore = create<SidebarState>((set) => ({
  // Main sidebar closed by default: user can open only when needed
  isMainSidebarOpen: getInitialMainSidebar(),
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

  isLeftPanelOpen: getStoredBoolean("asep_left_panel_open", true),
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

  isRightPanelOpen: getStoredBoolean("asep_right_panel_open", true),
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
      isMainSidebarOpen: false,
      isLeftPanelOpen: true,
      isRightPanelOpen: true,
    }),
}));
