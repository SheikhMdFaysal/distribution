import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Footer } from "@/components/Footer";

// Inline script applies the saved theme before React hydrates,
// preventing the flash-of-wrong-theme that hurts perceived quality.
const themeBootstrap = `(function(){try{var t=localStorage.getItem('ai-security-theme')||'system';var d=t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.classList.toggle('dark',d);document.documentElement.dataset.theme=d?'dark':'light';}catch(e){}})();`;

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Enterprise AI Security Red Teaming Platform",
  description:
    "Stress-test AI models for security vulnerabilities and compliance risks. INFO 588 Capstone, Feliciano School of Business, Montclair State University.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // suppressHydrationWarning silences false positives caused by browser extensions
    // (e.g. Grammarly's data-gr-* attributes) that mutate the DOM before React hydrates.
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </head>
      <body className="min-h-full flex flex-col" suppressHydrationWarning>
        <div className="flex-1">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
