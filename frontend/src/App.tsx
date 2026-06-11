import { lazy, Suspense, type ReactNode } from "react";
import {
  createRootRoute,
  createRoute,
  createRouter,
  Navigate,
  RouterProvider,
} from "@tanstack/react-router";

import { AuthGate } from "./app/auth";
import { AppProviders } from "./app/providers";
import { AppShell } from "./components/layout/app-shell";

const AssistantPage = lazy(() =>
  import("./features/assistant/assistant-page").then((module) => ({
    default: module.AssistantPage,
  })),
);
const AuditPage = lazy(() =>
  import("./features/audit/audit-page").then((module) => ({ default: module.AuditPage })),
);
const HelpPage = lazy(() =>
  import("./features/help/help-page").then((module) => ({ default: module.HelpPage })),
);
const RetrievalPage = lazy(() =>
  import("./features/retrieval/retrieval-page").then((module) => ({
    default: module.RetrievalPage,
  })),
);
const ReviewsPage = lazy(() =>
  import("./features/reviews/reviews-page").then((module) => ({ default: module.ReviewsPage })),
);
const SchemasPage = lazy(() =>
  import("./features/schemas/schemas-page").then((module) => ({ default: module.SchemasPage })),
);
const SettingsPage = lazy(() =>
  import("./features/settings/settings-page").then((module) => ({
    default: module.SettingsPage,
  })),
);
const WorkbenchPage = lazy(() =>
  import("./features/workbench/workbench-page").then((module) => ({
    default: module.WorkbenchPage,
  })),
);
const WorkflowsPage = lazy(() =>
  import("./features/workflows/workflows-page").then((module) => ({
    default: module.WorkflowsPage,
  })),
);

const rootRoute = createRootRoute({
  component: () => (
    <AuthGate>
      <AppShell />
    </AuthGate>
  ),
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: () => <Navigate to="/assistant" />,
});

const workflowsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workflows",
  component: () => (
    <RouteSuspense>
      <WorkflowsPage />
    </RouteSuspense>
  ),
});

const assistantRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/assistant",
  component: () => (
    <RouteSuspense>
      <AssistantPage />
    </RouteSuspense>
  ),
});

const workflowDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workflows/$workflowId",
  component: function WorkflowDetailRoute() {
    const { workflowId } = workflowDetailRoute.useParams();
    return (
      <RouteSuspense>
        <WorkflowsPage workflowId={workflowId} />
      </RouteSuspense>
    );
  },
});

const reviewsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/reviews",
  component: () => (
    <RouteSuspense>
      <ReviewsPage />
    </RouteSuspense>
  ),
});

const retrievalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/retrieval",
  component: () => (
    <RouteSuspense>
      <RetrievalPage />
    </RouteSuspense>
  ),
});

const auditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/audit",
  component: () => (
    <RouteSuspense>
      <AuditPage />
    </RouteSuspense>
  ),
});

const schemasRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/schemas",
  component: () => (
    <RouteSuspense>
      <SchemasPage />
    </RouteSuspense>
  ),
});

const workbenchRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workbench",
  component: () => (
    <RouteSuspense>
      <WorkbenchPage />
    </RouteSuspense>
  ),
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/settings",
  component: () => (
    <RouteSuspense>
      <SettingsPage />
    </RouteSuspense>
  ),
});

const helpRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/help",
  component: () => (
    <RouteSuspense>
      <HelpPage mode="overview" />
    </RouteSuspense>
  ),
});

const helpTutorialsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/help/tutorials",
  component: () => (
    <RouteSuspense>
      <HelpPage mode="tutorials" />
    </RouteSuspense>
  ),
});

const helpManualRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/help/manual",
  component: () => (
    <RouteSuspense>
      <HelpPage mode="manual" />
    </RouteSuspense>
  ),
});

const authCallbackRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/auth/callback",
  component: () => <Navigate to="/assistant" />,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  assistantRoute,
  workflowsRoute,
  workflowDetailRoute,
  reviewsRoute,
  retrievalRoute,
  auditRoute,
  schemasRoute,
  workbenchRoute,
  settingsRoute,
  helpRoute,
  helpTutorialsRoute,
  helpManualRoute,
  authCallbackRoute,
]);

const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

function App() {
  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  );
}

function RouteSuspense({ children }: { children: ReactNode }) {
  return <Suspense fallback={<RouteLoading />}>{children}</Suspense>;
}

function RouteLoading() {
  return (
    <div className="grid min-h-[320px] place-items-center p-6">
      <div className="rounded-md border border-border bg-card px-4 py-3 text-sm font-semibold text-muted-foreground shadow-sm">
        Loading route
      </div>
    </div>
  );
}

export default App;
