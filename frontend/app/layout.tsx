import type { Metadata } from "next";
import { B612, Orbitron } from "next/font/google";
import "./globals.css";

const displayFont = Orbitron({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700", "800"],
});

const bodyFont = B612({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "700"],
});

export const metadata: Metadata = {
  title: "Holocron Timeline Engine",
  description: "Interactive Star Wars knowledge graph and timeline explorer",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${displayFont.variable} ${bodyFont.variable}`}>{children}</body>
    </html>
  );
}
