import * as React from "react";

export type LabelProps = any;

export const Label = React.forwardRef(function Label(
  { className, ...props }: any,
  ref: any
) {
  return (
    <label
      ref={ref}
      className={["mb-1 block text-xs font-medium text-muted-foreground", className]
        .filter(Boolean)
        .join(" ")}
      {...props}
    />
  );
});

