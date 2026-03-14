import * as React from "react";

export type AlertProps = {
  variant?: "default" | "destructive";
  className?: string;
  [key: string]: any;
};

export function Alert({ variant = "default", className, ...props }: AlertProps) {
  const base =
    "relative w-full rounded-lg border p-4 text-sm [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg+div]:ml-8";
  const variantClass =
    variant === "destructive"
      ? "border-red-500/80 bg-red-50 text-red-900"
      : "border border-border bg-background text-foreground";

  return (
    <div
      role="alert"
      className={[base, variantClass, className].filter(Boolean).join(" ")}
      {...props}
    />
  );
}

export function AlertTitle({ className, ...props }: any) {
  return (
    <h5
      className={["mb-1 font-semibold leading-none tracking-tight", className]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
}

export function AlertDescription({ className, ...props }: any) {
  return (
    <p
      className={["text-sm opacity-90", className].filter(Boolean).join(" ")}
      {...props}
    />
  );
}

