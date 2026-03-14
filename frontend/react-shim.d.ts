declare module "react" {
  export type ReactNode = any;
  export interface FC<P = {}> {
    (props: P): ReactNode | null;
  }

  export interface HTMLAttributes<T> {
    className?: string;
    [key: string]: any;
  }

  export interface InputHTMLAttributes<T> extends HTMLAttributes<T> {}
  export interface ButtonHTMLAttributes<T> extends HTMLAttributes<T> {}
  export interface LabelHTMLAttributes<T> extends HTMLAttributes<T> {}
  export interface HTMLDivElement {}
  export interface HTMLHeadingElement {}
  export interface HTMLParagraphElement {}
  export interface HTMLLabelElement {}
  export interface HTMLButtonElement {}
  export interface HTMLInputElement {}

  export interface FormEvent<T = any> {
    preventDefault(): void;
    target: T;
  }

  export function forwardRef<T, P = {}>(
    render: (props: P, ref: any) => ReactNode | null
  ): (props: P & { ref?: any }) => ReactNode | null;

  export function useState<S>(initial: S): [S, (value: S) => void];
  export function useMemo<T>(factory: () => T, deps: any[]): T;
}

declare module "lucide-react" {
  export const AlertCircle: any;
  export const Info: any;
  export const TriangleAlert: any;
}


