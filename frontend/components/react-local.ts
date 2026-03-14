export type ReactNode = any;

export function useState<S>(initial: S): [S, (value: S) => void] {
  let state = initial;
  const setState = (value: S) => {
    state = value;
  };
  return [state, setState];
}

export function useMemo<T>(factory: () => T, _deps: any[]): T {
  return factory();
}

export function forwardRef<T, P = {}>(
  render: (props: P, ref: any) => ReactNode | null
): (props: P & { ref?: any }) => ReactNode | null {
  return function Forwarded(props: P & { ref?: any }) {
    return render(props, props.ref);
  };
}

