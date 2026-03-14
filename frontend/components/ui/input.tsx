import * as React from "react";

export type InputProps = any;

export const Input = React.forwardRef(function Input(
  { className, ...props }: any,
  ref: any
) {
  return (
    <input
      ref={ref}
      className={["flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-sm outline-none", className]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
});

