import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Claims Adjudication - AI-Powered Multi-Agent System',
  description: 'Real-time claims adjudication using multi-agent AI workflow',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
