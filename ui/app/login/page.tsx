"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { AuthShell } from "@/components/auth/auth-shell";
import { Field, PasswordField } from "@/components/auth/fields";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorState } from "@/components/app/states";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { signIn, status } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "authenticated") router.replace("/app");
  }, [status, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(email.trim(), password);
      router.replace("/app");
    } catch (caught) {
      setError((caught as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Sign in"
      subtitle="Pick up where your themes left off."
      footer={
        <>
          No account yet?{" "}
          <Link href="/signup" className="text-primary underline-offset-4 hover:underline">
            Create one
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
          label="Password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
          disabled={submitting}
        />

        <Button type="submit" size="lg" disabled={submitting} className="mt-1">
          {submitting && <Loader2 className="size-4 animate-spin" aria-hidden />}
          {submitting ? "Signing in" : "Sign in"}
        </Button>

        {/* Honest about a real consequence: the backend rotates the workspace
            key on every login, so another signed-in tab or device stops
            working the moment this succeeds. Being bounced out with no
            explanation reads as a bug. */}
        <p className="text-xs leading-relaxed text-muted-foreground">
          Signing in issues a new key for your workspace. If you are signed in
          on another device or tab, that session ends.
        </p>
      </form>
    </AuthShell>
  );
}
