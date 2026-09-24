import * as RadixLabel from "@radix-ui/react-label";
import type { ReactNode } from "react";

export function Field({
  id,
  label,
  error,
  hint,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  hint?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <RadixLabel.Root htmlFor={id} className="text-sm font-medium text-foreground">
          {label}
        </RadixLabel.Root>
        {hint}
      </div>
      {children}
      {error && (
        <p role="alert" className="text-xs font-medium text-danger">
          {error}
        </p>
      )}
    </div>
  );
}
