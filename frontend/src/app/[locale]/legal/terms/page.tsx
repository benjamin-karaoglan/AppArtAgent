import { useTranslations } from 'next-intl'
import { getTranslations } from 'next-intl/server'
import { FileText } from 'lucide-react'
import type { Metadata } from 'next'

type Props = { params: Promise<{ locale: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'legal.terms' })
  return { title: t('title') }
}

export default function TermsOfServicePage() {
  const t = useTranslations('legal.terms')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <div className="flex items-center gap-3 mb-2">
          <FileText className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
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
