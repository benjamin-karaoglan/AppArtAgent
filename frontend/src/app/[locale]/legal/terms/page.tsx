'use client'

import { useTranslations, useLocale } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/navigation'
import { FileText, Globe } from 'lucide-react'

export default function TermsOfServicePage() {
  const t = useTranslations('legal.terms')
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()

  const switchLocale = (newLocale: string) => {
    router.replace(pathname, { locale: newLocale as 'fr' | 'en' })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <FileText className="w-8 h-8 text-primary-600" />
            <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
          </div>
          <button
            onClick={() => switchLocale(locale === 'fr' ? 'en' : 'fr')}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            title={locale === 'fr' ? 'Switch to English' : 'Passer en français'}
          >
            <Globe className="w-4 h-4" />
            {locale === 'fr' ? 'EN' : 'FR'}
          </button>
        </div>
        <p className="text-sm text-gray-500 mb-8">{t('lastUpdated')}</p>

        <div className="prose prose-gray max-w-none space-y-8">
          <p>{t('intro')}</p>

          <section>
            <h2>{t('service.title')}</h2>
            <p>{t('service.content')}</p>
          </section>

          <section>
            <h2>{t('aiDisclaimer.title')}</h2>
            <p>{t('aiDisclaimer.content')}</p>
          </section>

          <section>
            <h2>{t('userResponsibilities.title')}</h2>
            <ul>
              <li>{t('userResponsibilities.accurate')}</li>
              <li>{t('userResponsibilities.lawful')}</li>
              <li>{t('userResponsibilities.credentials')}</li>
              <li>{t('userResponsibilities.rights')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('ip.title')}</h2>
            <p>{t('ip.userContent')}</p>
            <p>{t('ip.aiContent')}</p>
            <p>{t('ip.platform')}</p>
          </section>

          <section>
            <h2>{t('availability.title')}</h2>
            <p>{t('availability.content')}</p>
          </section>

          <section>
            <h2>{t('liability.title')}</h2>
            <p>{t('liability.content')}</p>
          </section>

          <section>
            <h2>{t('termination.title')}</h2>
            <p>{t('termination.content')}</p>
          </section>

          <section>
            <h2>{t('law.title')}</h2>
            <p>{t('law.content')}</p>
          </section>

          <section>
            <h2>{t('changes.title')}</h2>
            <p>{t('changes.content')}</p>
          </section>

          <p className="text-sm text-gray-500 mt-8">
            Contact: <a href={`mailto:${t('contactEmail')}`} className="text-primary-600 hover:underline">{t('contactEmail')}</a>
          </p>
        </div>
      </div>
    </div>
  )
}
