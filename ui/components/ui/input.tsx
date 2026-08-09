import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        // h-11 on touch: the 44px minimum target, and it stops iOS zooming on
        // focus when paired with a 16px base size.
        "flex h-11 w-full min-w-0 rounded-md border border-input bg-surface px-3 py-2 text-base shadow-xs transition-[color,box-shadow,border-color] outline-none sm:h-9 sm:text-sm",
        "placeholder:text-muted-foreground/70",
        "file:inline-flex file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground",
        "focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/45",
        "aria-invalid:border-destructive aria-invalid:ring-destructive/25",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
}

export { Input }
