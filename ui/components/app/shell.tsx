"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Boxes,
  History,
  Layers,
  LogOut,
  Menu,
  Play,
  Search,
  Settings,
  Component,
  LayoutDashboard,
  Upload,
  X,
} from "lucide-react";

import dynamic from "next/dynamic";

// Renders nothing until opened, so cmdk stays out of every page's first
// load. The shortcut lives in its own module and still works immediately.
const CommandMenu = dynamic(
  () => import("@/components/app/command-menu").then((m) => m.CommandMenu),
  { ssr: false },
);
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Logo } from "@/components/logo";
import { useAuth } from "@/lib/auth";
import { useCommandMenu } from "@/lib/use-command-menu";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/app/overview", label: "Overview", icon: LayoutDashboard, exact: false },
  { href: "/app", label: "Analyze", icon: Play, exact: true },
  { href: "/app/themes", label: "Themes", icon: Layers, exact: false },
  { href: "/app/areas", label: "Areas", icon: Component, exact: false },
  { href: "/app/explore", label: "Explore", icon: Boxes, exact: false },
  { href: "/app/runs", label: "Runs", icon: History, exact: false },
  { href: "/app/ingest", label: "Upload", icon: Upload, exact: false },
  { href: "/app/settings", label: "Settings", icon: Settings, exact: false },
];

function isActive(pathname: string, href: string, exact: boolean) {
  return exact ? pathname === href : pathname.startsWith(href);
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { status, email, workspace, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const { open: commandOpen, setOpen: setCommandOpen } = useCommandMenu();

  const currentLabel =
    [...NAV].reverse().find((item) => isActive(pathname, item.href, item.exact))
      ?.label ?? "Analyze";

  // Rendered after mount only: reading the platform during SSR would emit
  // the wrong glyph and hydrate mismatched.
  const [modifierKey, setModifierKey] = useState("Ctrl ");
  useEffect(() => {
    if (navigator.platform.toLowerCase().includes("mac")) setModifierKey("⌘");
  }, []);

  useEffect(() => {
    if (status === "anonymous") router.replace("/login");
  }, [status, router]);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  if (status !== "authenticated") {
    return (
      <div className="grid min-h-dvh place-items-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Logo className="size-8 animate-pulse" />
          <p className="text-sm text-muted-foreground">
            {status === "loading" ? "Checking your session" : "Redirecting to sign in"}
          </p>
        </div>
      </div>
    );
  }

  // A workspace created by the CLI has a key but no user, so email is null.
  // Fall back to the workspace name rather than rendering an empty identity.
  const identity = email ?? workspace?.name ?? "Workspace";

  const navList = (
    <ul className="grid gap-0.5">
      {NAV.map((item) => {
        const active = isActive(pathname, item.href, item.exact);
        return (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                // Without this the browser's default outline lands here — a
                // hard white box on a dark sidebar that reads as a rendering
                // bug. Keep a visible ring (removing it would break keyboard
                // navigation), just the themed one used everywhere else.
                "focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring",
                active
                  ? "bg-secondary font-medium text-foreground"
                  : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground",
              )}
            >
              <item.icon className="size-4 shrink-0" aria-hidden />
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );

  return (
    <div className="min-h-dvh bg-background lg:grid lg:grid-cols-[15rem_1fr]">
      {/* Sidebar for large screens, per adaptive navigation guidance. */}
      <aside className="sticky top-0 hidden h-dvh flex-col border-r border-border bg-surface-2/40 px-3 py-4 lg:flex">
        <Link
          href="/app"
          className="mb-6 flex items-center gap-2.5 px-2 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring"
        >
          <Logo className="size-6" />
          <span className="font-display text-[15px] font-semibold tracking-tight">
            Sentilytics
          </span>
        </Link>

        <nav aria-label="Product" className="flex-1">
          {navList}
        </nav>

        <div className="border-t border-border pt-3">
          <p className="truncate px-3 text-xs text-muted-foreground" title={identity}>
            {identity}
          </p>
          <div className="mt-2 flex items-center gap-1 px-1">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="sm"
              className="flex-1 justify-start text-muted-foreground"
              onClick={signOut}
            >
              <LogOut className="size-4" aria-hidden />
              Sign out
            </Button>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        {/*
          Desktop top bar. Deliberately quiet: where you are, one way to
          search, nothing else. Page-level actions belong to the page header
          below it, not up here competing with navigation.
        */}
        <header className="sticky top-0 z-30 hidden h-14 items-center justify-between gap-4 border-b border-border bg-background/85 px-6 backdrop-blur lg:flex">
          <nav aria-label="Breadcrumb" className="min-w-0">
            <ol className="flex items-center gap-2 text-sm">
              <li className="text-muted-foreground">{workspace?.name ?? "Workspace"}</li>
              <li className="text-muted-foreground/50" aria-hidden>
                /
              </li>
              <li className="font-medium text-foreground">{currentLabel}</li>
            </ol>
          </nav>

          <button
            type="button"
            onClick={() => setCommandOpen(true)}
            className="interactive flex items-center gap-2 rounded-md border border-border px-2.5 py-1.5 text-sm text-muted-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            <Search className="size-3.5" aria-hidden />
            <span className="pr-6">Search</span>
            <kbd className="type-meta rounded border border-border px-1.5 py-0.5">
              {modifierKey}K
            </kbd>
          </button>
        </header>

        {/* Top bar for small screens. */}
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-border bg-background/90 px-4 backdrop-blur lg:hidden">
          <Link href="/app" className="flex items-center gap-2">
            <Logo className="size-5" />
            <span className="font-display text-sm font-semibold tracking-tight">
              Sentilytics
            </span>
          </Link>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((value) => !value)}
            >
              {menuOpen ? <X className="size-4" /> : <Menu className="size-4" />}
            </Button>
          </div>
        </header>

        {menuOpen && (
          <div className="border-b border-border bg-surface px-3 py-3 lg:hidden">
            <nav aria-label="Product">{navList}</nav>
            <div className="mt-3 flex items-center justify-between border-t border-border px-3 pt-3">
              <span className="truncate text-xs text-muted-foreground">{identity}</span>
              <Button variant="ghost" size="sm" onClick={signOut}>
                <LogOut className="size-4" aria-hidden />
                Sign out
              </Button>
            </div>
          </div>
        )}

        <main className="min-w-0 flex-1">{children}</main>
      </div>

      <CommandMenu open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-5 py-6 sm:px-8">
      <div className="min-w-0">
        <h1 className="font-display text-xl font-semibold tracking-tight sm:text-2xl">
          {title}
        </h1>
        {description && (
          <p className="mt-1.5 max-w-[70ch] text-sm text-muted-foreground">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}
