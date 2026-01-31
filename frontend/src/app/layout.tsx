import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/Providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AppArt Agent - Smart Property Decisions',
  description: 'AI-powered platform to help you make informed apartment purchasing decisions in France',
  openGraph: {
    title: 'AppArt Agent - Smart Property Decisions',
    description: 'AI-powered platform to help you make informed apartment purchasing decisions in France',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AppArt Agent - Smart Property Decisions',
    description: 'AI-powered platform to help you make informed apartment purchasing decisions in France',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
