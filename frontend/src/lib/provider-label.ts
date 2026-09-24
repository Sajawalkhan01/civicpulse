export interface ProviderPresentation {
  label: string;
  isFallback: boolean;
  description: string;
}

/** `triaged_by` on ComplaintOut is whichever provider actually produced the
 * result: the configured provider's name (rules, simulated, llm:groq, ...),
 * or "rules:fallback" when the real provider failed and the service fell
 * back to the deterministic rules engine (see triage_service.py). Falling
 * back is a designed safety net, not an error -- it's presented as a normal,
 * slightly different outcome, not a warning. */
export function presentProvider(triagedBy: string | null): ProviderPresentation {
  if (triagedBy === "rules:fallback") {
    return {
      label: "Backup rules",
      isFallback: true,
      description: "The AI triage service wasn't available for this one, so a fast rules engine handled it instantly instead.",
    };
  }
  if (triagedBy === "rules") {
    return { label: "Rules engine", isFallback: false, description: "Triaged by CivicPulse's deterministic rules engine." };
  }
  if (triagedBy === "simulated") {
    return { label: "Simulated AI", isFallback: false, description: "Triaged by the simulated triage provider (dev/demo mode)." };
  }
  if (triagedBy?.startsWith("llm")) {
    return { label: "AI triage", isFallback: false, description: `Triaged by ${triagedBy}.` };
  }
  return { label: triagedBy ?? "Unknown", isFallback: false, description: "" };
}
