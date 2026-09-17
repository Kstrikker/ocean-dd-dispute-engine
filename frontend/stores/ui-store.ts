"use client";

import { create } from "zustand";

interface UiState {
  sidebarCollapsed: boolean;
  mobileNavigationOpen: boolean;
  toggleSidebar: () => void;
  setMobileNavigationOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>((set) => ({
  sidebarCollapsed: false,
  mobileNavigationOpen: false,
  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setMobileNavigationOpen: (mobileNavigationOpen) =>
    set({ mobileNavigationOpen }),
}));
