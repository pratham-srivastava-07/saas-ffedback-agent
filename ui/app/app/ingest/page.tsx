"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { FileUp, Upload } from "lucide-react";

import { PageHeader } from "@/components/app/shell";
import { ErrorState } from "@/components/app/states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, MAX_ITEMS, SOURCES, type Source } from "@/lib/api";

/**
 * CSV upload.
 *
 * Real feedback arrives as an export from Zendesk or Intercom, not as a
 * hand-built JSON array. Only the text column is mandatory — the backend falls
 * back rather than rejecting an upload over an unrecognised tier or source,
 * so the mapping fields below are hints, not requirements.
 */
export default function IngestPage() {
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
  const [textColumn, setTextColumn] = useState("text");
  const [userTypeColumn, setUserTypeColumn] = useState("user_type");
  const [sourceColumn, setSourceColumn] = useState("source");
  const [idColumn, setIdColumn] = useState("id");
  const [defaultSource, setDefaultSource] = useState<Source>("other");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;

    setSubmitting(true);
    setError(null);

    const form = new FormData();
    form.append("file", file);
    form.append("text_column", textColumn.trim() || "text");
    form.append("user_type_column", userTypeColumn.trim() || "user_type");
    form.append("source_column", sourceColumn.trim() || "source");
    form.append("id_column", idColumn.trim() || "id");
    form.append("default_source", defaultSource);

    try {
      const result = await api.analyzeCsv(form);
      router.push(`/app/runs/${encodeURIComponent(result.run_id)}`);
    } catch (caught) {
      setError((caught as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Upload"
        description="Analyse a CSV export. The first row must be a header."
      />

      <form
        onSubmit={submit}
        className="grid max-w-5xl gap-6 px-5 py-6 sm:px-8 lg:grid-cols-2 lg:items-start"
      >
        <section className="rounded-lg border bg-surface p-5">
          <Label htmlFor="csv-file" className="font-display text-sm font-semibold">
            CSV file
          </Label>

          <label
            htmlFor="csv-file"
            className="mt-3 flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-border px-6 py-10 text-center transition-colors hover:border-primary/50 hover:bg-muted/30 focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-ring"
          >
            <FileUp className="size-6 text-muted-foreground" aria-hidden />
            <span className="mt-3 text-sm font-medium">
              {file ? file.name : "Choose a CSV file"}
            </span>
            <span className="mt-1 font-mono text-[11px] text-muted-foreground tabular">
              {file
                ? `${(file.size / 1024).toFixed(1)} KB`
                : `up to ${MAX_ITEMS} rows per upload`}
            </span>
            <input
              id="csv-file"
              type="file"
              accept=".csv,text/csv"
              className="sr-only"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setError(null);
              }}
            />
          </label>
        </section>

        <section className="rounded-lg border bg-surface p-5">
          <h2 className="font-display text-sm font-semibold">Column mapping</h2>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Which columns in your file hold each field. Only the text column has
            to exist.
          </p>

          {/* Single column: this card now sits in a half-width grid track,
              where side-by-side inputs would be cramped. */}
          <div className="mt-4 grid gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="text-column">Text column (required)</Label>
              <Input
                id="text-column"
                value={textColumn}
                onChange={(event) => setTextColumn(event.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="id-column">ID column</Label>
              <Input
                id="id-column"
                value={idColumn}
                onChange={(event) => setIdColumn(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="user-type-column">Customer tier column</Label>
              <Input
                id="user-type-column"
                value={userTypeColumn}
                onChange={(event) => setUserTypeColumn(event.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Values should read free, paid or enterprise.
              </p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="source-column">Source column</Label>
              <Input
                id="source-column"
                value={sourceColumn}
                onChange={(event) => setSourceColumn(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="default-source">Fallback source</Label>
              <select
                id="default-source"
                value={defaultSource}
                onChange={(event) =>
                  setDefaultSource(event.target.value as Source)
                }
                className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                {SOURCES.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground">
                Used for rows with no recognisable source.
              </p>
            </div>
          </div>
        </section>

        {error && <ErrorState message={error} className="lg:col-span-2" />}

        <div className="flex items-center gap-3 lg:col-span-2">
          <Button type="submit" disabled={!file || submitting}>
            <Upload className="size-3.5" aria-hidden />
            {submitting ? "Analysing..." : "Analyse CSV"}
          </Button>
          <p className="text-xs text-muted-foreground">
            {submitting
              ? "This runs the full pipeline and can take a minute."
              : "You will land on the run when it finishes."}
          </p>
        </div>
      </form>
    </>
  );
}
