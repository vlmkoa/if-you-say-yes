import "./globals.css";
import Link from "next/link";
import { Plus_Jakarta_Sans } from "next/font/google";

const fontSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata = {
  title: "If You Say Yes",
  description: "Drug interaction checker and substance profile dashboard.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={fontSans.variable}>
      <body className="min-h-screen bg-slate-950 font-sans text-slate-100 antialiased">
        <div className="relative min-h-screen overflow-x-hidden">
          <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-20%,rgba(34,211,238,0.15),transparent),radial-gradient(ellipse_60%_50%_at_100%_100%,rgba(16,185,129,0.08),transparent)]" />

          <header className="sticky top-0 z-50 border-b border-white/[0.08] bg-slate-950/70 backdrop-blur-xl">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 sm:py-4">
              <Link href="/" className="flex items-center gap-3 transition-opacity hover:opacity-90">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/20 text-sm font-bold text-cyan-300 shadow-[0_0_20px_-5px_rgba(34,211,238,0.2)]">
                  IY
                </div>
                <div>
                  <span className="block text-sm font-semibold tracking-tight text-white">If You Say Yes</span>
                  <span className="block text-xs text-slate-500">Interaction intelligence</span>
                </div>
              </Link>

              <nav className="flex items-center gap-1 text-sm">
                <Link
                  href="/"
                  className="rounded-lg px-3 py-2 text-slate-400 transition-colors hover:bg-white/5 hover:text-white sm:px-4"
                >
                  Home
                </Link>
                <Link
                  href="/dashboard"
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-slate-300 transition-colors hover:border-cyan-400/30 hover:bg-cyan-400/10 hover:text-cyan-200 sm:px-4"
                >
                  Dashboard
                </Link>
                <Link
                  href="/reagent"
                  className="rounded-lg px-3 py-2 text-slate-400 transition-colors hover:bg-white/5 hover:text-white sm:px-4"
                >
                  Reagent test
                </Link>
              </nav>
            </div>
          </header>

          <main className="relative">{children}</main>

          <footer className="border-t border-white/[0.08] bg-slate-950/50">
            <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-slate-500 sm:px-6 md:flex-row md:items-center md:justify-between md:py-8">
              <p>Built for safer substance exploration and interaction awareness.</p>
              <p className="md:text-right">For educational use only — not a substitute for clinical judgment.</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
