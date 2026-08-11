"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  Boxes,
  History,
  Layers,
  LayoutDashboard,
  Play,
  Search,
  Settings,
  Upload,
} from "lucide-react";

import { api, type ThemeListItem } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * Cmd-K navigation.
 *
 * Themes are the only entity worth searching by name — runs are identified by
 * date and there are never many pages. They load once when the palette first
 * opens rather than on mount, so the cost falls on people who use it.
 */

const ROUTES = [
  { href: "/app/overview", label: "Overview", icon: LayoutDashboard },
  { href: "/app", label: "Analyze feedback", icon: Play },
  { href: "/app/themes", label: "Themes", icon: Layers },
  { href: "/app/explore", label: "Explore clusters", icon: Boxes },
  { href: "/app/runs", label: "Runs", icon: History },
  { href: "/app/ingest", label: "Upload CSV", icon: Upload },
  { href: "/app/settings", label: "Settings", icon: Settings },
];

export function CommandMenu({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();
  const [themes, setThemes] = useState<ThemeListItem[] | null>(null);

  useEffect(() => {
    if (!open || themes !== null) return;
    let cancelled = false;
    api
      .themes(100)
      .then((result) => {
        if (!cancelled) setThemes(result);
      })
      // Navigation must still work if the fetch fails; an empty list is a
      // perfectly usable palette.
      .catch(() => {
        if (!cancelled) setThemes([]);
      });
    return () => {
      cancelled = true;
    };
  }, [open, themes]);

  function go(href: string) {
    onOpenChange(false);
    router.push(href);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center px-4 pt-[12vh]"
      role="presentation"
      onClick={() => onOpenChange(false)}
    >
      <div className="absolute inset-0 bg-background/70 backdrop-blur-[2px]" />

      <Command
        label="Command menu"
        loop
        className="floating relative w-full max-w-xl overflow-hidden rounded-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center gap-2.5 border-b border-border px-4">
          <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          <Command.Input
            autoFocus
            placeholder="Jump to a page or theme"
            className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
          />
          <kbd className="type-meta rounded border border-border px-1.5 py-0.5 text-muted-foreground">
            esc
          </kbd>
        </div>

        <Command.List className="max-h-[22rem] overflow-y-auto p-2">
          <Command.Empty className="px-3 py-8 text-center text-sm text-muted-foreground">
            No matches
          </Command.Empty>

          <Command.Group
            heading="Go to"
            className="[&_[cmdk-group-heading]]:type-meta [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-muted-foreground"
          >
            {ROUTES.map((route) => (
              <Item key={route.href} onSelect={() => go(route.href)}>
                <route.icon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                {route.label}
              </Item>
            ))}
          </Command.Group>

          {themes && themes.length > 0 && (
            <Command.Group
              heading="Themes"
              className="mt-1 [&_[cmdk-group-heading]]:type-meta [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-muted-foreground"
            >
              {themes.map((theme) => (
                <Item
                  key={theme.id}
                  value={`theme ${theme.name}`}
                  onSelect={() => go(`/app/themes/${encodeURIComponent(theme.id)}`)}
                >
                  <Layers className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                  <span className="min-w-0 flex-1 truncate">{theme.name}</span>
                  <span className="type-meta shrink-0 text-muted-foreground">
                    {theme.total_mentions}
                  </span>
                </Item>
              ))}
            </Command.Group>
          )}
        </Command.List>
      </Command>
    </div>
  );
}

function Item({
  children,
  onSelect,
  value,
}: {
  children: React.ReactNode;
  onSelect: () => void;
  value?: string;
}) {
  return (
    <Command.Item
      value={value}
      onSelect={onSelect}
      className={cn(
        "flex cursor-pointer items-center gap-2.5 rounded-md px-2.5 py-2 text-sm",
        "data-[selected=true]:bg-surface-hover data-[selected=true]:text-foreground",
      )}
    >
      {children}
    </Command.Item>
  );
}
