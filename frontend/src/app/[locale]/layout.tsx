import { Inter } from 'next/font/google'
import { NextIntlClientProvider, hasLocale } from 'next-intl'
import { getMessages, getTranslations } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'
import { Providers } from '@/components/Providers'
import CookieConsent from '@/components/ui/CookieConsent'
import FeedbackButton from '@/components/ui/FeedbackButton'
import Footer from '@/components/ui/Footer'
import type { Metadata, Viewport } from 'next'
import '../globals.css'

const inter = Inter({ subsets: ['latin'] })

type Props = {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }))
}

export const viewport: Viewport = {
  themeColor: '#2563eb',
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'metadata' })

  return {
    title: t('title'),
    description: t('description'),
    manifest: '/manifest.json',
    appleWebApp: {
      capable: true,
      statusBarStyle: 'default',
      title: 'AppArt Agent',
    },
    icons: {
      icon: '/icon.svg',
      apple: '/icons/apple-touch-icon.png',
    },
    openGraph: {
      title: t('ogTitle'),
      description: t('ogDescription'),
    },
    alternates: {
      languages: {
        fr: '/fr',
        en: '/en',
      },
    },
  }
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params
  if (!hasLocale(routing.locales, locale)) {
    notFound()
  }

  const messages = await getMessages()

  return (
    <html lang={locale}>
      <body className={`${inter.className} flex flex-col min-h-screen`}>
        <NextIntlClientProvider messages={messages}>
          <Providers>
            <div className="flex-1">
              {children}
            </div>
            <Footer />
            <FeedbackButton />
            <CookieConsent />
          </Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
