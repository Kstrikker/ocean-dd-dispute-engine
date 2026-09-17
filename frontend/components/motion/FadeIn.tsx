"use client";

import type { ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

import { cn } from "@/lib/utils";

interface FadeInProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  once?: boolean;
}

export function FadeIn({ children, className, delay = 0, once = true }: FadeInProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      className={cn(className)}
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      transition={{ duration: reduceMotion ? 0 : 0.65, delay, ease: "easeOut" }}
      viewport={{ once, amount: 0.25 }}
    >
      {children}
    </motion.div>
  );
}
