import * as React from "react";

export type ButtonProps = any;

export const Button = React.forwardRef(function Button(
  { className, ...props }: any,
  ref: any
) {
  return (
    <button
      ref={ref}
      className={[
        "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
});

