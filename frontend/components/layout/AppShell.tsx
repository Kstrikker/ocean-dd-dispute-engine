import type { ReactNode } from "react";
import Link from "next/link";
import { Anchor } from "lucide-react";

import { Navbar } from "@/components/layout/Navbar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Navbar />
      <main id="main-content" className="flex-1">
        {children}
      </main>
      <footer className="border-t bg-slate-950 px-5 py-10 text-slate-300 dark:bg-slate-950">
        <div className="mx-auto flex max-w-[1500px] flex-col justify-between gap-8 sm:flex-row sm:items-end">
          <div>
            <Link href="/" className="focus-ring inline-flex items-center gap-2 rounded-md font-semibold text-white">
              <Anchor aria-hidden="true" className="size-5 text-cyan-400" /> Ocean D&amp;D
            </Link>
            <p className="mt-3 max-w-md text-sm leading-6 text-slate-400">
              Evidence-compiled, deterministically calculated ocean-freight dispute intelligence.
            </p>
          </div>
          <p className="text-xs text-slate-500">Human approval required before every dispute action.</p>
        </div>
      </footer>
    </div>
  );
}
