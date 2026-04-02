'use client'

import { useTranslations } from 'next-intl'
import Link from 'next/link'

export default function Footer() {
  const t = useTranslations('footer')

  return (
    <footer className="bg-gray-900 text-white py-6 mt-auto">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="text-center sm:text-left">
            <p className="text-sm">{t('copyright')}</p>
            <p className="text-gray-400 text-xs mt-0.5">{t('tagline')}</p>
          </div>
          <nav className="flex items-center gap-6 text-sm text-gray-400">
            <Link href="/legal/privacy" className="hover:text-white transition-colors">
              {t('privacy')}
            </Link>
            <Link href="/legal/terms" className="hover:text-white transition-colors">
              {t('terms')}
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  )
}
