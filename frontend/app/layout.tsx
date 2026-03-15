import "./globals.css";
import Link from "next/link";
import { Plus_Jakarta_Sans } from "next/font/google";
import { DisclaimerGate } from "@/components/DisclaimerGate";
import { MainNav } from "@/components/MainNav";

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
      <body className="min-h-screen bg-amber-50 font-sans text-slate-900 antialiased">
        <div className="relative min-h-screen overflow-x-hidden">
          <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,rgba(248,113,113,0.28),transparent_55%),radial-gradient(circle_at_top_right,rgba(244,114,182,0.26),transparent_55%),radial-gradient(circle_at_bottom_left,rgba(251,191,36,0.24),transparent_55%),radial-gradient(circle_at_bottom_right,rgba(254,249,195,0.6),transparent_65%)]" />

          <header className="sticky top-0 z-50 group">
            <div className="w-full border-b border-slate-900/60 bg-slate-900/20 backdrop-blur-md transition-colors group-hover:bg-slate-900/70">
              <div className="mx-auto max-w-6xl px-4 sm:px-6">
                <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-2 py-3 sm:py-4">
                  <Link href="/" className="transition-opacity hover:opacity-90">
                    <span className="block text-2xl font-semibold tracking-tight text-amber-50 sm:text-3xl">
                      If you say &quot;Yes&quot;
                    </span>
                  </Link>

                  <div className="flex justify-center">
                    <MainNav />
                  </div>

                  <div className="hidden sm:block w-12" aria-hidden="true" />
                </div>
              </div>
            </div>
          </header>

          <main className="relative">
            <DisclaimerGate>{children}</DisclaimerGate>
          </main>

          <footer className="border-t border-amber-200 bg-amber-50/80">
            <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-6 text-sm text-slate-700 sm:px-6 md:flex-row md:items-center md:justify-between md:py-8">
              <p>Built for harm reduction, overdose prevention, and substance interaction awareness.</p>
              <p className="md:text-right">For educational use only — not a substitute for clinical judgment.</p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}

