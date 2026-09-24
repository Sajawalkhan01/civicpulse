import { useEffect, useRef, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Sparkles, CheckCircle2, Info } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { CategoryBadge, PriorityBadge } from "@/components/badges";
import { createComplaint, ApiError } from "@/api/complaints";
import type { ComplaintOut } from "@/api/types";
import { LOCATION_MAX, TEXT_MAX, validateComplaintForm, type ComplaintFormErrors } from "@/lib/validation";
import { presentProvider } from "@/lib/provider-label";

const TRIAGE_PHRASES = [
  "Reading your report…",
  "Classifying the issue…",
  "Estimating priority…",
  "Almost done…",
];

interface FormState {
  text: string;
  location: string;
  reporterContact: string;
}

const EMPTY_FORM: FormState = { text: "", location: "", reporterContact: "" };

/** The actual submit form + result -- no outer page padding, so it can be
 * used both as the full /submit page (via SubmitPage below) and embedded
 * directly on the Home page's "try it live" section, without doubling up
 * on page-level margins. */
export function ComplaintForm() {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [errors, setErrors] = useState<ComplaintFormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ComplaintOut | null>(null);
  const [phraseIndex, setPhraseIndex] = useState(0);

  useEffect(() => {
    if (!submitting) return;
    setPhraseIndex(0);
    const interval = setInterval(() => {
      setPhraseIndex((i) => Math.min(i + 1, TRIAGE_PHRASES.length - 1));
    }, 1100);
    return () => clearInterval(interval);
  }, [submitting]);

  const textRef = useRef<HTMLTextAreaElement>(null);
  const locationRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const fieldErrors = validateComplaintForm({ text: form.text, location: form.location });
    setErrors(fieldErrors);
    if (fieldErrors.text) {
      textRef.current?.focus();
      return;
    }
    if (fieldErrors.location) {
      locationRef.current?.focus();
      return;
    }

    setSubmitting(true);
    try {
      const complaint = await createComplaint({
        text: form.text.trim(),
        location: form.location.trim(),
        reporter_contact: form.reporterContact.trim() || null,
      });
      setResult(complaint);
      toast.success("Complaint submitted");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(err.message);
      } else {
        toast.error("Couldn't reach CivicPulse. Please check your connection and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleSubmitAnother() {
    setForm(EMPTY_FORM);
    setErrors({});
    setResult(null);
  }

  if (result) {
    return <SubmitResult complaint={result} onReset={handleSubmitAnother} />;
  }

  return (
    <>
      <header className="mb-8">
        <h1 className="font-display text-3xl font-semibold text-foreground">Report a civic issue</h1>
        <p className="mt-2 text-muted-foreground">
          Tell us what's wrong and where — our triage system will route it to the right team automatically.
        </p>
      </header>

      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-6" aria-busy={submitting}>
        <Field
          id="complaint-text"
          label="What's the issue?"
          error={errors.text}
          hint={
            <span className="text-xs text-muted-foreground">
              {form.text.trim().length}/{TEXT_MAX}
            </span>
          }
        >
          <textarea
            ref={textRef}
            id="complaint-text"
            name="text"
            rows={5}
            disabled={submitting}
            value={form.text}
            onChange={(e) => setForm((f) => ({ ...f, text: e.target.value }))}
            placeholder="e.g. There's a burst water pipe flooding the sidewalk on Elm Street, right outside the bakery."
            aria-invalid={Boolean(errors.text)}
            aria-describedby={errors.text ? "complaint-text-error" : undefined}
            className="min-h-32 w-full resize-y rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
          />
        </Field>

        <Field
          id="complaint-location"
          label="Location"
          error={errors.location}
          hint={
            <span className="text-xs text-muted-foreground">
              {form.location.trim().length}/{LOCATION_MAX}
            </span>
          }
        >
          <input
            ref={locationRef}
            id="complaint-location"
            name="location"
            type="text"
            disabled={submitting}
            value={form.location}
            onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
            placeholder="e.g. 400 Elm Street, near the bakery"
            aria-invalid={Boolean(errors.location)}
            aria-describedby={errors.location ? "complaint-location-error" : undefined}
            className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
          />
        </Field>

        <Field id="complaint-contact" label="Contact (optional)">
          <input
            id="complaint-contact"
            name="reporterContact"
            type="text"
            disabled={submitting}
            value={form.reporterContact}
            onChange={(e) => setForm((f) => ({ ...f, reporterContact: e.target.value }))}
            placeholder="Phone or email, if you'd like an update"
            className="h-10 w-full rounded-lg border border-border bg-surface px-3 text-sm text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-60"
          />
        </Field>

        <AnimatePresence mode="wait">
          {submitting ? (
            <motion.div
              key="triaging"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              role="status"
              className="flex items-center gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3 text-sm text-primary"
            >
              <Sparkles className="h-4 w-4 shrink-0 animate-pulse" aria-hidden="true" />
              <span>
                <span className="font-medium">AI is triaging your complaint…</span>{" "}
                <span className="text-primary/80">{TRIAGE_PHRASES[phraseIndex]}</span>
              </span>
            </motion.div>
          ) : null}
        </AnimatePresence>

        <Button type="submit" size="lg" disabled={submitting}>
          {submitting ? "Triaging…" : "Submit complaint"}
        </Button>
      </form>
    </>
  );
}

function SubmitResult({ complaint, onReset }: { complaint: ComplaintOut; onReset: () => void }) {
  const provider = presentProvider(complaint.triaged_by);

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
      <div className="rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <div className="mb-4 flex items-center gap-2 text-success">
          <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
          <span className="text-sm font-medium">Complaint submitted</span>
        </div>

        <h1 className="font-display text-2xl font-semibold text-foreground">Thanks — we've got it.</h1>

        <div className="mt-5 flex flex-wrap gap-2">
          <CategoryBadge category={complaint.category} />
          <PriorityBadge priority={complaint.priority} />
        </div>

        {complaint.ai_summary && (
          <p className="mt-4 rounded-lg bg-surface-2 p-4 text-sm leading-relaxed text-foreground">{complaint.ai_summary}</p>
        )}

        <div
          data-testid="provider-note"
          className={
            provider.isFallback
              ? "mt-4 flex items-start gap-2 rounded-lg border border-accent/40 bg-accent/10 p-3 text-xs text-accent-foreground"
              : "mt-4 flex items-start gap-2 rounded-lg bg-surface-2 p-3 text-xs text-muted-foreground"
          }
        >
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span>
            <span className="font-medium">{provider.label}.</span> {provider.description}
          </span>
        </div>

        <Button onClick={onReset} variant="outline" className="mt-6 w-full">
          Submit another complaint
        </Button>
      </div>
    </motion.div>
  );
}

/** The real, full /submit route -- just ComplaintForm inside the standard
 * page-level max-width/padding shell. */
export default function SubmitPage() {
  return (
    <div className="mx-auto max-w-xl px-4 py-10 sm:px-6">
      <ComplaintForm />
    </div>
  );
}
