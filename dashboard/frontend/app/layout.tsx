import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WasteNet Research Dashboard",
  description: "Live waste detection, model evaluation, decision-gating, and robotic sorting research dashboard.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
