import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agentic Payments — Behavioural Risk Intelligence",
  description:
    "Visa, Mastercard, Stripe Radar trained on humans. Agents transact in tenths of a cent — invisible to those models. We built the behavioural risk layer for agentic payment rails.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" style={{ colorScheme: "dark" }}>
      <body className="font-sans">
        <header className="sticky top-0 z-50 border-b border-ink-700 bg-ink-900/70 backdrop-blur">
          <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-4 md:px-10">
            <Link
              href="/"
              className="text-sm font-semibold tracking-tight text-ink-50 md:text-base"
            >
              Agentic Payments
              <span className="ml-2 hidden text-ink-500 md:inline">
                · Behavioural Risk Intelligence
              </span>
            </Link>
            <nav className="flex items-center gap-5 text-sm text-ink-300">
              <a href="#demo" className="hover:text-ink-50">
                Demo
              </a>
              <a href="#memos" className="hover:text-ink-50">
                Memos
              </a>
              <a
                href="https://github.com/guernicastars/agentic-payments"
                target="_blank"
                rel="noreferrer"
                className="hover:text-ink-50"
              >
                GitHub
              </a>
            </nav>
          </div>
        </header>
        {children}
      </body>
    </html>
  );
}
