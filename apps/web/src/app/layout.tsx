import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LeadOps | Local lead management",
  description: "A local workspace for managing B2B prospects.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col" suppressHydrationWarning>{children}</body>
    </html>
  );
}
