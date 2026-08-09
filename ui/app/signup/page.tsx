"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { AuthShell } from "@/components/auth/auth-shell";
import { Field, MIN_PASSWORD_LENGTH, PasswordField } from "@/components/auth/fields";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorState } from "@/components/app/states";
import { useAuth } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();
  const { signUp, status } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/app");
  }, [status, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    // Validated here so the rule is learned before the round trip, not
    // discovered through a 422.
    if (password.length < MIN_PASSWORD_LENGTH) {
      setPasswordError(`Use at least ${MIN_PASSWORD_LENGTH} characters.`);
      document.getElementById("password")?.focus();
      return;
    }
    setPasswordError(null);
    setSubmitting(true);

    try {
      await signUp(email.trim(), password, workspaceName.trim() || undefined);
      router.replace("/app");
    } catch (caught) {
      setError((caught as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Create account"
      subtitle="You get a workspace of your own. Themes and trends stay inside it."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="text-primary underline-offset-4 hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="grid gap-5" noValidate>
        {error && <ErrorState message={error} />}

        <Field label="Email" htmlFor="email">
          <Input
            id="email"
            type="email"
            value={email}
            required
            autoComplete="email"
            autoFocus
            disabled={submitting}
            onChange={(event) => setEmail(event.target.value)}
          />
        </Field>

        <PasswordField
          id="password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          error={passwordError ?? undefined}
          hint={`At least ${MIN_PASSWORD_LENGTH} characters.`}
          disabled={submitting}
        />

        <Field
          label="Workspace name"
          htmlFor="workspace"
          hint="Optional. Named after your email if you leave it blank."
        >
          <Input
            id="workspace"
            value={workspaceName}
            disabled={submitting}
            autoComplete="organization"
            onChange={(event) => setWorkspaceName(event.target.value)}
          />
        </Field>

        <Button type="submit" size="lg" disabled={submitting} className="mt-1">
          {submitting && <Loader2 className="size-4 animate-spin" aria-hidden />}
          {submitting ? "Creating account" : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}
