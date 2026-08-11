"use client";

import { useEffect, useState } from "react";

/**
 * Owns the Cmd-K / Ctrl-K binding.
 *
 * Deliberately separate from the palette component: the shell needs this hook
 * on every page, but the palette itself pulls in cmdk and renders nothing
 * until opened. Keeping them apart lets the component be loaded on demand
 * while the shortcut still works from the first paint.
 */
export function useCommandMenu() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setOpen((value) => !value);
      }
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, []);

  return { open, setOpen };
}
