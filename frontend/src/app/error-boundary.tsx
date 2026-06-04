import * as React from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";

import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";

type AppErrorBoundaryProps = {
  children: React.ReactNode;
};

type AppErrorBoundaryState = {
  error: Error | null;
  resetKey: number;
};

export class AppErrorBoundary extends React.Component<
  AppErrorBoundaryProps,
  AppErrorBoundaryState
> {
  state: AppErrorBoundaryState = {
    error: null,
    resetKey: 0,
  };

  static getDerivedStateFromError(error: Error): Partial<AppErrorBoundaryState> {
    return { error };
  }

  reset = () => {
    this.setState((state) => ({
      error: null,
      resetKey: state.resetKey + 1,
    }));
  };

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
          <Card className="w-full max-w-xl">
            <CardHeader className="border-b border-border">
              <div className="flex items-start gap-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-red-50 text-red-700">
                  <AlertTriangle className="h-4 w-4" />
                </span>
                <div className="min-w-0">
                  <CardTitle>Application error</CardTitle>
                  <p className="mt-1 text-sm text-muted-foreground">
                    The console hit an unexpected rendering failure.
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 pt-4 sm:pt-5">
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900">
                {this.state.error.message || "Unknown application error"}
              </div>
              <Button className="w-fit" onClick={this.reset} type="button">
                <RotateCcw className="h-4 w-4" />
                Reset view
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }

    return <React.Fragment key={this.state.resetKey}>{this.props.children}</React.Fragment>;
  }
}
