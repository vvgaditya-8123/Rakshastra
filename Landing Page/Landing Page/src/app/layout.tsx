import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Playfair_Display } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { TransitionProvider } from "@/components/ThemeToggle";
import SmoothScrollProvider from "@/components/SmoothScrollProvider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

const playfairDisplay = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Rakshastra — Autonomous Cyber Defense Agent",
  description:
    "Rakshastra (रक्षास्त्र) is an AI-powered autonomous cyber defense agent that detects, maps, and disrupts digital narcotic networks across Telegram, WhatsApp, and Instagram.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} ${playfairDisplay.variable}`}
      suppressHydrationWarning
    >
      <body>
        <ThemeProvider>
          <TransitionProvider>
            <SmoothScrollProvider>
              {/* Ambient background orbs */}
              <div className="ambient-bg">
                <div className="ambient-orb orb-1"></div>
                <div className="ambient-orb orb-2"></div>
                <div className="ambient-orb orb-3"></div>
              </div>
              <div className="grid-overlay"></div>

              {children}
            </SmoothScrollProvider>
          </TransitionProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
