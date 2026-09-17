"use client";

import { useState, type FormEvent } from "react";
import { ArrowRight, CheckCircle2, Clock3, Mail, MapPin } from "lucide-react";
import { motion } from "framer-motion";

import { FadeIn } from "@/components/motion/FadeIn";
import { SlideUp } from "@/components/motion/SlideUp";
import { Button } from "@/components/ui/button";

const fieldClassName = "focus-ring mt-2 w-full rounded-lg border bg-background px-4 py-3 text-sm shadow-sm transition-all duration-200 placeholder:text-muted-foreground/70 hover:border-primary/40 focus:border-primary focus:shadow-[0_0_0_4px_rgba(59,130,246,0.1)]";

export default function ContactPage() {
  const [validated, setValidated] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    setValidated(true);
  };

  return (
    <div className="relative overflow-hidden px-5 py-16 sm:px-8 lg:px-12 lg:py-24">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[560px] bg-[radial-gradient(circle_at_22%_12%,rgba(14,165,233,0.15),transparent_32%),radial-gradient(circle_at_82%_8%,rgba(37,99,235,0.11),transparent_28%)]" />
      <div className="mx-auto grid max-w-[1300px] gap-14 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
        <FadeIn>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">Contact</p>
          <h1 className="mt-4 text-balance text-4xl font-semibold tracking-[-0.04em] sm:text-6xl">Bring us your hardest freight workflow.</h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground sm:text-lg">
            Tell us where invoice review breaks down today. We will map the evidence, controls, and deterministic logic needed for an operator-ready deployment.
          </p>

          <div className="mt-10 space-y-5">
            {[
              [Mail, "Enterprise enquiries", "Architecture, pilots, and integrations"],
              [Clock3, "Response window", "One business day for qualified requests"],
              [MapPin, "Delivery model", "Remote-first forward deployment"],
            ].map(([Icon, title, detail]) => (
              <div key={String(title)} className="flex gap-4">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Icon aria-hidden="true" className="size-5" />
                </span>
                <div>
                  <p className="text-sm font-semibold">{String(title)}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{String(detail)}</p>
                </div>
              </div>
            ))}
          </div>
        </FadeIn>

        <SlideUp>
          <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }} className="rounded-2xl border bg-card p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)] sm:p-9">
            {validated ? (
              <div role="status" className="flex min-h-[480px] flex-col items-center justify-center text-center">
                <span className="flex size-14 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 aria-hidden="true" className="size-7" />
                </span>
                <h2 className="mt-5 text-2xl font-semibold">Request validated</h2>
                <p className="mt-3 max-w-md text-sm leading-6 text-muted-foreground">
                  The form is ready for connection to your CRM or support endpoint before production deployment.
                </p>
                <Button variant="outline" className="mt-6" onClick={() => setValidated(false)}>Edit request</Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <h2 className="text-2xl font-semibold tracking-tight">Request a technical walkthrough</h2>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">Share enough context for us to understand the operational stakes.</p>
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <label className="text-sm font-medium">Name
                    <input name="name" autoComplete="name" required className={fieldClassName} placeholder="Your name" />
                  </label>
                  <label className="text-sm font-medium">Work email
                    <input name="email" type="email" autoComplete="email" required className={fieldClassName} placeholder="you@company.com" />
                  </label>
                </div>

                <label className="block text-sm font-medium">Company
                  <input name="company" autoComplete="organization" required className={fieldClassName} placeholder="Company name" />
                </label>

                <label className="block text-sm font-medium">Primary workflow
                  <select name="workflow" required defaultValue="" className={fieldClassName}>
                    <option value="" disabled>Select a workflow</option>
                    <option value="invoice-audit">D&amp;D invoice audit</option>
                    <option value="tariff-rag">Tariff and contract intelligence</option>
                    <option value="dispute-operations">Dispute operations</option>
                    <option value="integration">Enterprise integration</option>
                  </select>
                </label>

                <label className="block text-sm font-medium">What is happening today?
                  <textarea name="message" required rows={5} className={fieldClassName} placeholder="Describe the current process, document volume, and risk..." />
                </label>

                <Button type="submit" size="lg" className="group w-full sm:w-auto">
                  Request walkthrough <ArrowRight aria-hidden="true" className="transition-transform group-hover:translate-x-1" />
                </Button>
              </form>
            )}
          </motion.div>
        </SlideUp>
      </div>
    </div>
  );
}
