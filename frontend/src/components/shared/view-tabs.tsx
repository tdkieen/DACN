"use client";

import { cn } from "@/lib/utils";

interface ViewTabsProps<T extends string> {
  tabs: { id: T; label: string }[];
  value: T;
  onChange: (id: T) => void;
  label: string;
}

export function ViewTabs<T extends string>({ tabs, value, onChange, label }: ViewTabsProps<T>) {
  return (
    <div role="tablist" aria-label={label} className="mb-4 inline-flex rounded-md border bg-card p-1">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          aria-selected={value === t.id}
          onClick={() => onChange(t.id)}
          className={cn(
            "rounded-sm px-3 py-1.5 text-sm transition-colors",
            value === t.id ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
          )}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
