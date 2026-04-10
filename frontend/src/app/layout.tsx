import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Bitcoin Investment AI | Auto-Invest Bot",
  description: "Auto-invest Bitcoin setiap hari — Beli bila jatuh, Jual bila naik. Powered by Luno Malaysia.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ms">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
