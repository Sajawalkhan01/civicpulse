import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled error in CivicPulse UI", error, info.componentStack);
  }

  private reset = () => this.setState({ error: null });

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-background px-6">
          <div className="max-w-md rounded-2xl border border-border bg-surface p-8 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-danger-bg text-danger">
              <AlertTriangle className="h-6 w-6" aria-hidden="true" />
            </div>
            <h1 className="font-display text-xl font-semibold text-foreground">Something went wrong</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              This part of CivicPulse hit a snag. Your data is safe — try reloading this section.
            </p>
            <div className="mt-6 flex justify-center gap-3">
              <button
                type="button"
                onClick={this.reset}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:bg-primary-hover"
              >
                Try again
              </button>
              <button
                type="button"
                onClick={() => window.location.assign("/")}
                className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition hover:bg-surface-2"
              >
                Go home
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
