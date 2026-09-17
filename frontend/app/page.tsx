import Link from "next/link";
import { ArrowRight, Bot, CalendarClock, DatabaseZap, FileCheck2, Scale, ShieldCheck } from "lucide-react";

import { MaritimeHero } from "@/components/marketing/MaritimeHero";
import { FadeIn } from "@/components/motion/FadeIn";
import { SlideUp } from "@/components/motion/SlideUp";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: DatabaseZap,
    title: "Deterministic FDE Engine",
    description: "Python reconstructs the charge clock one date at a time. The model extracts evidence; it never performs billable-day or monetary calculations.",
  },
  {
    icon: ShieldCheck,
    title: "FMC-aware controls",
    description: "Case timelines, invoice metadata, dispute windows, and supporting evidence remain visible to operators throughout the review.",
  },
  {
    icon: CalendarClock,
    title: "Automated day ledger",
    description: "Every free, impeded, and chargeable date receives a rate, reason code, rule reference, and replayable calculation trail.",
  },
];

const workflow = [
  { number: "01", icon: Bot, title: "Compile evidence", detail: "Schema-constrained extraction turns PDFs into typed facts with source references." },
  { number: "02", icon: Scale, title: "Replay the rules", detail: "The deterministic engine applies free time, date boundaries, and tariff tiers." },
  { number: "03", icon: FileCheck2, title: "Approve the finding", detail: "Operations reviews the ledger and signs off before any dispute action." },
];

export default function HomePage() {
  return (
    <div className="overflow-hidden">
      <MaritimeHero />

      <section aria-label="Platform principles" className="border-y bg-card">
        <div className="mx-auto grid max-w-[1500px] divide-y px-5 sm:grid-cols-3 sm:divide-x sm:divide-y-0 sm:px-8 lg:px-12">
          {[
            ["30 days", "Invoice issuance control"],
            ["30 days", "Minimum dispute window"],
            ["0", "LLM-calculated dollars"],
          ].map(([value, label]) => (
            <div key={label} className="py-7 text-center sm:px-6">
              <p className="text-2xl font-semibold tracking-tight text-primary">{value}</p>
              <p className="mt-1 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="platform" className="relative px-5 py-24 sm:px-8 lg:px-12 lg:py-32">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(14,165,233,0.08),transparent_28%),radial-gradient(circle_at_90%_70%,rgba(37,99,235,0.08),transparent_30%)]" />
        <div className="relative mx-auto max-w-[1500px]">
          <FadeIn className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">Built for defensibility</p>
            <h2 className="mt-4 text-balance text-3xl font-semibold tracking-[-0.035em] sm:text-5xl">
              An evidence compiler in front. A deterministic engine underneath.
            </h2>
            <p className="mt-5 text-pretty text-base leading-7 text-muted-foreground sm:text-lg">
              The system separates interpretation from calculation, giving teams the speed of foundational models without surrendering control of financial logic.
            </p>
          </FadeIn>

          <div className="mt-14 grid gap-5 lg:grid-cols-3">
            {features.map((feature, index) => (
              <SlideUp key={feature.title} delay={index * 0.1} className="h-full">
                <article className="group h-full rounded-2xl border bg-card p-7 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-primary/35 hover:shadow-[0_24px_70px_rgba(15,23,42,0.1)] dark:hover:shadow-[0_24px_70px_rgba(2,132,199,0.08)]">
                  <span className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary transition-transform duration-300 group-hover:scale-105">
                    <feature.icon aria-hidden="true" className="size-5" />
                  </span>
                  <h3 className="mt-6 text-xl font-semibold tracking-tight">{feature.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{feature.description}</p>
                </article>
              </SlideUp>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-slate-950 px-5 py-24 text-white sm:px-8 lg:px-12 lg:py-32">
        <div className="mx-auto max-w-[1500px]">
          <SlideUp className="max-w-3xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">Operational workflow</p>
            <h2 className="mt-4 text-3xl font-semibold tracking-[-0.035em] sm:text-5xl">From raw PDF to reviewable dispute.</h2>
          </SlideUp>
          <div className="mt-14 grid gap-5 lg:grid-cols-3">
            {workflow.map((item, index) => (
              <SlideUp key={item.number} delay={index * 0.1}>
                <article className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.045] p-7 backdrop-blur-sm">
                  <span className="absolute right-5 top-3 text-6xl font-semibold tracking-tighter text-white/[0.045]">{item.number}</span>
                  <item.icon aria-hidden="true" className="size-6 text-cyan-400" />
                  <h3 className="mt-8 text-xl font-semibold">{item.title}</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-400">{item.detail}</p>
                </article>
              </SlideUp>
            ))}
          </div>
        </div>
      </section>

      <section className="px-5 py-24 sm:px-8 lg:px-12 lg:py-32">
        <SlideUp className="mx-auto max-w-5xl overflow-hidden rounded-3xl border bg-[linear-gradient(135deg,#0f172a,#0c4a6e)] px-6 py-14 text-center text-white shadow-[0_35px_100px_rgba(2,132,199,0.22)] sm:px-12 sm:py-20">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-300">Ready for a controlled review?</p>
          <h2 className="mx-auto mt-4 max-w-3xl text-balance text-3xl font-semibold tracking-[-0.035em] sm:text-5xl">Put your first invoice through the deterministic ledger.</h2>
          <p className="mx-auto mt-5 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">Upload a PDF, monitor the evidence compilation job, and inspect every date behind the final variance.</p>
          <Button asChild size="lg" className="group mt-8 bg-white text-slate-950 shadow-[0_0_36px_rgba(255,255,255,0.25)] hover:bg-cyan-50">
            <Link href="/dashboard">Launch the application <ArrowRight aria-hidden="true" className="transition-transform group-hover:translate-x-1" /></Link>
          </Button>
        </SlideUp>
      </section>
    </div>
  );
}
