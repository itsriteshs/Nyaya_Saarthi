import type { Metadata } from "next";
import { Cormorant_Garamond, Manrope } from "next/font/google";
import { MatterProvider } from "@/providers/MatterProvider";
import "./globals.css";

const editorial = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-serif",
  display: "swap",
});

const sans = Manrope({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "NyayaSaarthi",
  description: "A multilingual Motor Vehicle Law guidance prototype for India.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-scroll-behavior="smooth">
      <body className={`${editorial.variable} ${sans.variable} antialiased`}>
        <MatterProvider>{children}</MatterProvider>
      </body>
    </html>
  );
}
