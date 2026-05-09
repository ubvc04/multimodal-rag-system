import type { ReactNode } from "react";
import { Component } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-3xl border border-black/10 bg-white p-8 shadow-lg">
          <h2 className="font-display text-2xl">Something went wrong</h2>
          <p className="mt-2 text-sm text-black/60">Please refresh the page or try again.</p>
        </div>
      );
    }

    return this.props.children;
  }
}
