"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import { Anchor, ArrowUpRight, Menu, X } from "lucide-react";

import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Overview", href: "/" },
  { name: "Launch App", href: "/dashboard" },
  { name: "Contact", href: "/contact" },
];

function Brand() {
  return (
    <Link href="/" className="focus-ring flex items-center gap-3 rounded-md" aria-label="Ocean D&D home">
      <span className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-[0_8px_24px_rgba(14,165,233,0.25)]">
        <Anchor aria-hidden="true" className="size-5" />
      </span>
      <span className="leading-tight">
        <span className="block text-sm font-semibold tracking-tight">Ocean D&amp;D</span>
        <span className="block text-[11px] text-muted-foreground">Dispute Engine</span>
      </span>
    </Link>
  );
}

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border/70 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <Brand />

        <nav aria-label="Primary navigation" className="hidden items-center gap-1 md:flex">
          {navigation.map((item) => {
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "focus-ring rounded-md px-4 py-2 text-sm font-medium transition-colors",
                  active ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                )}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button asChild size="sm" className="hidden sm:inline-flex">
            <Link href="/dashboard">
              Review invoice <ArrowUpRight aria-hidden="true" />
            </Link>
          </Button>

          <Dialog.Root open={mobileOpen} onOpenChange={setMobileOpen}>
            <Dialog.Trigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden" aria-label="Open navigation">
                <Menu aria-hidden="true" />
              </Button>
            </Dialog.Trigger>
            <Dialog.Portal>
              <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/55 backdrop-blur-sm" />
              <Dialog.Content className="fixed inset-y-0 right-0 z-50 w-[min(88vw,340px)] border-l bg-background p-6 shadow-2xl outline-none">
                <Dialog.Title className="sr-only">Site navigation</Dialog.Title>
                <div className="flex items-center justify-between">
                  <Brand />
                  <Dialog.Close asChild>
                    <Button variant="ghost" size="icon" aria-label="Close navigation">
                      <X aria-hidden="true" />
                    </Button>
                  </Dialog.Close>
                </div>
                <nav aria-label="Mobile navigation" className="mt-10 flex flex-col gap-2">
                  {navigation.map((item) => {
                    const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileOpen(false)}
                        aria-current={active ? "page" : undefined}
                        className={cn(
                          "focus-ring rounded-lg px-4 py-3 text-base font-medium",
                          active ? "bg-accent text-accent-foreground" : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                        )}
                      >
                        {item.name}
                      </Link>
                    );
                  })}
                </nav>
                <Button asChild className="mt-6 w-full">
                  <Link href="/dashboard" onClick={() => setMobileOpen(false)}>Launch dispute engine</Link>
                </Button>
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
        </div>
      </div>
    </header>
  );
}
