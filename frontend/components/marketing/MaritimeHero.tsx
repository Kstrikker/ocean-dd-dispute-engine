"use client";

import { useRef } from "react";
import Link from "next/link";
import { ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

function CargoShipIllustration() {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      animate={reduceMotion ? undefined : { y: [0, -8, 0], rotate: [0, 0.35, 0] }}
      transition={{ duration: 5.5, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      className="relative mx-auto w-full max-w-[720px] drop-shadow-[0_30px_55px_rgba(2,132,199,0.28)]"
    >
      <svg viewBox="0 0 900 430" role="img" aria-label="Cargo ship moving through stylized ocean waves" className="h-auto w-full">
        <defs>
          <linearGradient id="hull" x1="0" x2="1">
            <stop offset="0" stopColor="#0f172a" />
            <stop offset="1" stopColor="#1e3a5f" />
          </linearGradient>
          <linearGradient id="wake" x1="0" x2="1">
            <stop offset="0" stopColor="#38bdf8" stopOpacity="0" />
            <stop offset="0.5" stopColor="#7dd3fc" stopOpacity="0.8" />
            <stop offset="1" stopColor="#38bdf8" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d="M103 277h695l-78 88H218c-49 0-91-34-115-88Z" fill="url(#hull)" />
        <path d="M180 294h556" stroke="#38bdf8" strokeWidth="5" strokeLinecap="round" opacity="0.75" />
        <path d="M620 158h105v119H602V181c0-13 8-23 18-23Z" fill="#e2e8f0" />
        <path d="M642 178h52v28h-52Z" fill="#0ea5e9" opacity="0.85" />
        <path d="M690 126h9v35h-9Z" fill="#cbd5e1" />
        <path d="M699 129h51" stroke="#cbd5e1" strokeWidth="5" strokeLinecap="round" />
        {[
          [218, 205, "#2563eb"], [292, 205, "#0f766e"], [366, 205, "#475569"], [440, 205, "#0284c7"], [514, 205, "#1d4ed8"],
          [255, 151, "#0369a1"], [329, 151, "#334155"], [403, 151, "#0891b2"], [477, 151, "#1e40af"],
          [292, 97, "#0f766e"], [366, 97, "#2563eb"], [440, 97, "#475569"],
        ].map(([x, y, fill], index) => (
          <g key={index}>
            <rect x={Number(x)} y={Number(y)} width="66" height="46" rx="4" fill={String(fill)} />
            <path d={`M${Number(x) + 9} ${Number(y) + 8}v30M${Number(x) + 22} ${Number(y) + 8}v30M${Number(x) + 35} ${Number(y) + 8}v30M${Number(x) + 48} ${Number(y) + 8}v30`} stroke="#fff" strokeOpacity="0.2" strokeWidth="2" />
          </g>
        ))}
        <ellipse cx="454" cy="382" rx="330" ry="16" fill="url(#wake)" opacity="0.65" />
      </svg>
    </motion.div>
  );
}

export function MaritimeHero() {
  const containerRef = useRef<HTMLElement>(null);
  const reduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"],
  });
  const shipY = useTransform(scrollYProgress, [0, 1], [0, 130]);
  const shipX = useTransform(scrollYProgress, [0, 1], [0, 55]);
  const waterY = useTransform(scrollYProgress, [0, 1], [0, -34]);

  return (
    <section ref={containerRef} className="relative isolate min-h-[calc(100svh-4rem)] overflow-hidden bg-slate-950 text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_28%,rgba(14,165,233,0.2),transparent_34%),radial-gradient(circle_at_20%_16%,rgba(37,99,235,0.18),transparent_30%)]" />
      <div className="ocean-grid absolute inset-0 opacity-30" />

      <div className="relative mx-auto grid min-h-[calc(100svh-4rem)] max-w-[1500px] items-center gap-12 px-5 py-20 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:px-12">
        <motion.div
          initial={{ opacity: 0, y: reduceMotion ? 0 : 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.8, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 max-w-3xl"
        >
          <Badge className="mb-6 border-sky-400/30 bg-sky-400/10 text-sky-200 hover:bg-sky-400/10">
            <ShieldCheck aria-hidden="true" className="size-3.5" /> Evidence-first freight intelligence
          </Badge>
          <h1 className="text-balance text-5xl font-semibold tracking-[-0.045em] sm:text-6xl lg:text-7xl">
            Turn ocean freight invoices into
            <span className="block bg-gradient-to-r from-sky-300 via-cyan-200 to-blue-400 bg-clip-text text-transparent">defensible decisions.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-pretty text-base leading-7 text-slate-300 sm:text-lg sm:leading-8">
            Compile evidence with AI. Reconstruct every free and chargeable day with deterministic Python. Surface audit-ready D&amp;D disputes before money leaves the dock.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" className="group relative overflow-hidden bg-blue-500 text-white shadow-[0_0_34px_rgba(59,130,246,0.45)] hover:bg-blue-400">
              <Link href="/dashboard">
                Launch dispute engine
                <ArrowRight aria-hidden="true" className="transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="border-white/15 bg-white/5 text-white hover:bg-white/10 hover:text-white">
              <Link href="#platform">Explore the platform</Link>
            </Button>
          </div>
          <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-400">
            {["No LLM arithmetic", "Evidence-linked findings", "Human approval gate"].map((item) => (
              <span key={item} className="flex items-center gap-2">
                <CheckCircle2 aria-hidden="true" className="size-4 text-cyan-400" /> {item}
              </span>
            ))}
          </div>
        </motion.div>

        <motion.div
          style={reduceMotion ? undefined : { y: shipY, x: shipX }}
          className="relative z-10 lg:translate-x-8"
        >
          <CargoShipIllustration />
        </motion.div>
      </div>

      <motion.div style={reduceMotion ? undefined : { y: waterY }} className="pointer-events-none absolute inset-x-0 bottom-0 h-32">
        <svg viewBox="0 0 1440 180" preserveAspectRatio="none" className="h-full w-full" aria-hidden="true">
          <path d="M0 92c184 50 310-46 506-5 203 43 285 86 483 25 170-52 293-43 451 3v65H0Z" fill="#082f49" opacity="0.88" />
          <path d="M0 123c200-35 330 45 520 6 236-48 302-21 468 19 173 41 284-25 452-7v39H0Z" fill="#075985" opacity="0.75" />
        </svg>
      </motion.div>
    </section>
  );
}
