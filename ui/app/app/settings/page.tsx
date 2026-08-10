"use client";

import { useState } from "react";
import { Check, Copy, LogOut, TriangleAlert } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { API_BASE } from "@/lib/api";

export default function SettingsPage() {
  const { email, workspace, apiKey, signOut } = useAuth();
  const [copied, setCopied] = useState(false);
  const [revealed, setRevealed] = useState(false);

  async function copyKey() {
    if (!apiKey) return;
    await navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <>
      <PageHeader
        title="Settings"
        description="Your workspace and the key that authenticates it."
      />

      {/*
        Two columns from lg up. Auto-placement puts Workspace and Session in
        the left column and the taller API-key card on the right, which stops
        a 672px form stranding a thousand pixels of empty space beside it.
        `items-start` keeps each card its natural height rather than stretching
        the short ones to match.
      */}
      <div className="grid gap-6 px-5 py-6 sm:px-8 lg:grid-cols-2 lg:items-start xl:grid-cols-3">
        <section className="rounded-lg border bg-surface p-5">
          <h2 className="font-display text-sm font-semibold">Workspace</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Name</dt>
              <dd className="font-medium">{workspace?.name ?? "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Workspace ID</dt>
              <dd className="truncate font-mono text-xs">{workspace?.id ?? "—"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Signed in as</dt>
              {/* Null for workspaces made by the CLI, which have a key but no user. */}
              <dd className="font-medium">{email ?? "API key only"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">API endpoint</dt>
              <dd className="truncate font-mono text-xs">{API_BASE}</dd>
            </div>
          </dl>
        </section>

        <section className="rounded-lg border bg-surface p-5">
          <h2 className="font-display text-sm font-semibold">API key</h2>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Send this as an <code className="font-mono text-xs">X-API-Key</code>{" "}
            header to use the API directly.
          </p>

          <div className="mt-4 flex items-center gap-2">
            <code className="min-w-0 flex-1 truncate rounded-md border bg-muted/40 px-3 py-2 font-mono text-xs">
              {apiKey
                ? revealed
                  ? apiKey
                  : `${apiKey.slice(0, 8)}${"•".repeat(24)}`
                : "—"}
            </code>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setRevealed((value) => !value)}
              disabled={!apiKey}
            >
              {revealed ? "Hide" : "Reveal"}
            </Button>
            <Button variant="outline" size="sm" onClick={copyKey} disabled={!apiKey}>
              {copied ? (
                <Check className="size-3.5" aria-hidden />
              ) : (
                <Copy className="size-3.5" aria-hidden />
              )}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>

          {/*
            Not a disclaimer for its own sake: only the hash of a key is stored,
            so logging in cannot return the existing one — it issues a new key
            and retires the old. Someone signed out of another tab deserves to
            know why rather than reading it as a bug.
          */}
          <div className="mt-4 flex items-start gap-2.5 rounded-md border border-signal-new/30 bg-signal-new/5 px-3 py-2.5">
            <TriangleAlert
              className="mt-0.5 size-3.5 shrink-0 text-signal-new"
              aria-hidden
            />
            <p className="text-xs leading-relaxed text-muted-foreground">
              Signing in again — on another device or in another tab — issues a
              new key and immediately invalidates this one. Only a hash of the
              key is stored, so an existing key can never be shown to you twice.
            </p>
          </div>
        </section>

        <section className="rounded-lg border bg-surface p-5">
          <h2 className="font-display text-sm font-semibold">Session</h2>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Signing out clears the key from this browser. It stays valid
            elsewhere.
          </p>
          <Button variant="outline" size="sm" className="mt-4" onClick={signOut}>
            <LogOut className="size-3.5" aria-hidden />
            Sign out
          </Button>
        </section>
      </div>
    </>
  );
}
