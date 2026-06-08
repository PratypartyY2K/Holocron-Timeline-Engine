import type { Metadata } from "next";
import "./globals.css";

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
      <body>{children}</body>
    </html>
  );
}

