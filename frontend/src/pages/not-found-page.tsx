import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-4 py-24 text-center">
      <h1 className="font-display text-4xl font-semibold text-foreground">Page not found</h1>
      <p className="mt-3 text-muted-foreground">The page you're looking for doesn't exist.</p>
      <Link
        to="/"
        className="mt-6 inline-flex h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary-hover"
      >
        Back to CivicPulse
      </Link>
    </div>
  );
}
