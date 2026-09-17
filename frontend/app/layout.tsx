import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { Providers } from "@/components/Providers";

export const metadata: Metadata = {
  title: {
    default: "Ocean D&D Dispute Engine",
    template: "%s | Ocean D&D",
  },
  description: "Evidence-first ocean-freight detention and demurrage intelligence, calculated by deterministic rules.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <a
          href="#main-content"
          className="focus-ring fixed left-4 top-3 z-[100] -translate-y-20 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-transform focus:translate-y-0"
        >
          Skip to main content
        </a>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
