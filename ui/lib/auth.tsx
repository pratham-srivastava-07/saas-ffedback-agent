"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  api,
  onUnauthorized,
  readStoredKey,
  writeStoredKey,
  type Workspace,
} from "@/lib/api";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthState {
  status: Status;
  email: string | null;
  workspace: Workspace | null;
  apiKey: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (
    email: string,
    password: string,
    workspaceName?: string,
  ) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<Status>("loading");
  const [email, setEmail] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [apiKey, setApiKey] = useState<string | null>(null);

  const clear = useCallback(() => {
    writeStoredKey(null);
    setApiKey(null);
    setEmail(null);
    setWorkspace(null);
    setStatus("anonymous");
  }, []);

  // Any 401 anywhere in the app drops the key and returns to the signed-out
  // state. Registered once, globally, so no individual call site has to
  // remember to handle it.
  useEffect(() => {
    onUnauthorized(clear);
    return () => onUnauthorized(null);
  }, [clear]);

  // Validate a stored key on boot. A key that no longer works (login rotates
  // it) must not leave the app in a half-signed-in state.
  useEffect(() => {
    const stored = readStoredKey();
    if (!stored) {
      setStatus("anonymous");
      return;
    }

    let cancelled = false;
    setApiKey(stored);

    api
      .me()
      .then((me) => {
        if (cancelled) return;
        setEmail(me.email);
        setWorkspace(me.workspace);
        setStatus("authenticated");
      })
      .catch(() => {
        if (!cancelled) clear();
      });

    return () => {
      cancelled = true;
    };
  }, [clear]);

  const adopt = useCallback(
    (result: { api_key: string; email: string; workspace: Workspace }) => {
      writeStoredKey(result.api_key);
      setApiKey(result.api_key);
      setEmail(result.email);
      setWorkspace(result.workspace);
      setStatus("authenticated");
    },
    [],
  );

  const value = useMemo<AuthState>(
    () => ({
      status,
      email,
      workspace,
      apiKey,
      signIn: async (e, p) => adopt(await api.login(e, p)),
      signUp: async (e, p, name) => adopt(await api.signup(e, p, name)),
      signOut: clear,
    }),
    [status, email, workspace, apiKey, adopt, clear],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
