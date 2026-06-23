import * as React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Database, FileCheck2, Loader2, LogIn, ShieldCheck } from "lucide-react";

import {
  ApiRequestError,
  API_BASE_URL,
  AUTH_SESSION_EXPIRED_EVENT,
  acceptInvitation,
  completeGoogleLogin,
  getCurrentAuthSession,
  getGoogleAuthorizationUrl,
  logoutCurrentSession,
} from "../api";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import type { AuthUser } from "../types";

const PENDING_INVITE_KEY = "ojtflow:pending-invite-token";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  signIn: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = React.useState<AuthUser | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const callbackHandled = React.useRef(false);

  const expireSession = React.useCallback(() => {
    setUser(null);
    setError(null);
    queryClient.clear();
    setLoading(false);
    if (window.location.pathname !== "/") {
      window.history.replaceState({}, document.title, "/");
    }
  }, [queryClient]);

  React.useEffect(() => {
    const handleSessionExpired = () => expireSession();
    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () => {
      window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, handleSessionExpired);
    };
  }, [expireSession]);

  React.useEffect(() => {
    if (callbackHandled.current) return;
    callbackHandled.current = true;

    const sync = async () => {
      const url = new URL(window.location.href);
      const isCallback = url.pathname === "/auth/callback";
      const isInviteAccept = url.pathname === "/invite/accept";
      const inviteToken = url.searchParams.get("token");
      const callbackError = url.searchParams.get("error");
      const code = url.searchParams.get("code");
      const state = url.searchParams.get("state");
      setLoading(true);
      setError(null);
      try {
        if (callbackError) throw new Error(`Sign-in failed: ${callbackError}`);
        if (isCallback) {
          if (!code || !state) throw new Error("Sign-in callback is missing code or state.");
          const login = await completeGoogleLogin(code, state);
          setUser(login.user);
          const pendingInvite = sessionStorage.getItem(PENDING_INVITE_KEY);
          if (pendingInvite) {
            sessionStorage.removeItem(PENDING_INVITE_KEY);
            try {
              await acceptInvitation(pendingInvite);
            } catch (inviteError) {
              setError(inviteError instanceof Error ? inviteError.message : String(inviteError));
            }
            window.history.replaceState({}, document.title, "/settings");
          } else {
            window.history.replaceState({}, document.title, "/assistant");
          }
        } else if (isInviteAccept && inviteToken) {
          try {
            const session = await getCurrentAuthSession();
            await acceptInvitation(inviteToken);
            setUser(session.user);
            window.history.replaceState({}, document.title, "/settings");
          } catch (inviteError) {
            if (inviteError instanceof ApiRequestError && inviteError.status === 401) {
              // Not signed in yet: stash the token and route through Keycloak login.
              sessionStorage.setItem(PENDING_INVITE_KEY, inviteToken);
              const redirectUri = `${window.location.origin}/auth/callback`;
              const authUrl = await getGoogleAuthorizationUrl(redirectUri);
              window.location.assign(authUrl.authorization_url);
              return;
            }
            throw inviteError;
          }
        } else {
          const session = await getCurrentAuthSession();
          setUser(session.user);
        }
      } catch (err) {
        if (err instanceof ApiRequestError && err.status === 401) {
          expireSession();
        } else {
          setUser(null);
          setError(err instanceof Error ? err.message : String(err));
        }
        if (isCallback || isInviteAccept) {
          window.history.replaceState({}, document.title, "/");
        }
      } finally {
        setLoading(false);
      }
    };

    void sync();
  }, [expireSession]);

  const signIn = async () => {
    setLoading(true);
    setError(null);
    try {
      const redirectUri = `${window.location.origin}/auth/callback`;
      const authUrl = await getGoogleAuthorizationUrl(redirectUri);
      window.location.assign(authUrl.authorization_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await logoutCurrentSession();
    } catch {
      // Local UI state should still clear if the server token is already invalid.
    } finally {
      expireSession();
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, signIn, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = React.useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { user, loading, error, signIn } = useAuth();
  if (loading && !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <div className="grid w-full max-w-sm gap-3 rounded-lg border border-border bg-card p-4 text-sm shadow-[0_1px_3px_rgba(16,24,40,0.06)]">
          <div className="flex items-center gap-3">
            <BrandMark />
            <div className="min-w-0">
              <div className="font-extrabold">OJTFlow</div>
              <div className="text-xs text-muted-foreground">Checking session</div>
            </div>
            <Loader2 className="ml-auto h-4 w-4 animate-spin text-primary" />
          </div>
          <div className="rounded-lg border border-border/60 bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
            API <strong className="text-foreground">{API_BASE_URL}</strong>
          </div>
        </div>
      </div>
    );
  }
  if (!user) {
    return (
      <div className="min-h-screen bg-background">
        <main className="mx-auto grid min-h-screen w-full max-w-6xl items-center gap-8 p-4 sm:p-6 lg:grid-cols-[minmax(0,1fr)_440px]">
          <section className="grid gap-6">
            <div className="flex items-center gap-3">
              <BrandMark />
              <div className="min-w-0">
                <div className="text-lg font-extrabold">OJTFlow</div>
                <div className="text-sm text-muted-foreground">Healthcare data operations</div>
              </div>
            </div>
            <div className="max-w-2xl">
              <h1 className="text-3xl font-black leading-tight text-foreground sm:text-4xl">
                Sign in to continue
              </h1>
              <p className="mt-3 max-w-xl text-base leading-7 text-muted-foreground">
                Enter the governed workspace for review-gated healthcare data workflows,
                evidence, and audit trails.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <AccessFact
                icon={ShieldCheck}
                label="OAuth session"
                value="Keycloak SSO"
              />
              <AccessFact
                icon={Database}
                label="Access scope"
                value="Authenticated owner"
              />
              <AccessFact
                icon={FileCheck2}
                label="Review trail"
                value="Audit attached"
              />
            </div>
          </section>

          <Card className="w-full overflow-hidden">
            <CardHeader className="border-b border-border/60 bg-muted/30">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <CardTitle>Access boundary</CardTitle>
                  <CardDescription>Sign in with email or Google via Keycloak.</CardDescription>
                </div>
                <Badge variant="success">controlled</Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 pt-4 sm:pt-5">
              {error ? (
                <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
                  {error}
                </div>
              ) : null}
              <Button className="h-10" onClick={() => void signIn()} type="button">
                <LogIn className="h-4 w-4" />
                Sign in
              </Button>
              <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/60 p-3 text-xs">
                <div className="flex min-w-0 items-center justify-between gap-3">
                  <span className="font-bold uppercase text-muted-foreground">API</span>
                  <strong className="min-w-0 break-words text-right text-foreground">
                    {API_BASE_URL}
                  </strong>
                </div>
                <div className="flex min-w-0 items-center justify-between gap-3">
                  <span className="font-bold uppercase text-muted-foreground">Session</span>
                  <span className="text-right font-semibold text-foreground">HTTP-only cookie</span>
                </div>
                <div className="flex min-w-0 items-center justify-between gap-3">
                  <span className="font-bold uppercase text-muted-foreground">Scope</span>
                  <span className="text-right font-semibold text-foreground">Owner-bound data</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    );
  }
  return <>{children}</>;
}

function BrandMark() {
  return (
    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md bg-[#ccfbf1] text-lg font-black text-sidebar shadow-[0_8px_24px_rgba(45,212,191,0.16)]">
      OF
    </div>
  );
}

function AccessFact({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="grid gap-2 border-t border-border pt-3">
      <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary">
        <Icon className="h-4 w-4" />
      </span>
      <div>
        <div className="text-xs font-bold uppercase text-muted-foreground">{label}</div>
        <div className="mt-1 text-sm font-extrabold">{value}</div>
      </div>
    </div>
  );
}
