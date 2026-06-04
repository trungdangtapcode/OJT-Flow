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
import { AiChatPage } from "./features/ai/ai-chat-page";
import { AuditPage } from "./features/audit/audit-page";
import { ReviewsPage } from "./features/reviews/reviews-page";
import { SchemasPage } from "./features/schemas/schemas-page";
import { SettingsPage } from "./features/settings/settings-page";
import { WorkbenchPage } from "./features/workbench/workbench-page";
import { WorkflowsPage } from "./features/workflows/workflows-page";

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
  component: () => <Navigate to="/workflows" />,
});

const workflowsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workflows",
  component: () => <WorkflowsPage />,
});

const workflowDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workflows/$workflowId",
  component: function WorkflowDetailRoute() {
    const { workflowId } = workflowDetailRoute.useParams();
    return <WorkflowsPage workflowId={workflowId} />;
  },
});

const reviewsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/reviews",
  component: ReviewsPage,
});

const auditRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/audit",
  component: AuditPage,
});

const schemasRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/schemas",
  component: SchemasPage,
});

const workbenchRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/workbench",
  component: WorkbenchPage,
});

const aiRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/ai",
  component: AiChatPage,
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/settings",
  component: SettingsPage,
});

const authCallbackRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/auth/callback",
  component: () => <Navigate to="/workflows" />,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  workflowsRoute,
  workflowDetailRoute,
  reviewsRoute,
  auditRoute,
  schemasRoute,
  workbenchRoute,
  aiRoute,
  settingsRoute,
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

export default App;
