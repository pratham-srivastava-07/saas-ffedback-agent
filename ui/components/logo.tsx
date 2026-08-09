import { cn } from "@/lib/utils";

/**
 * Brand mark: scattered points with one cluster resolved. A single simple
 * geometric mark, which is the one case where drawing rather than importing
 * is the right call.
 */
export function Logo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={cn("shrink-0", className)}
      role="img"
      aria-label="Sentilytics"
    >
      <circle cx="4.5" cy="6" r="1.4" className="fill-muted-foreground/55" />
      <circle cx="19.4" cy="5.2" r="1.15" className="fill-muted-foreground/45" />
      <circle cx="20" cy="17.5" r="1.4" className="fill-muted-foreground/55" />
      <circle cx="5" cy="18.4" r="1.15" className="fill-muted-foreground/45" />
      <circle cx="10.6" cy="10.4" r="2" className="fill-primary" />
      <circle cx="14.6" cy="12.4" r="2.4" className="fill-primary" />
      <circle cx="11.2" cy="15" r="1.7" className="fill-primary/80" />
    </svg>
  );
}
