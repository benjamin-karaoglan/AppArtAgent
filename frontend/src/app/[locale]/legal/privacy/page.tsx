import { useTranslations } from 'next-intl'
import { getTranslations } from 'next-intl/server'
import { Shield } from 'lucide-react'
import type { Metadata } from 'next'

type Props = { params: Promise<{ locale: string }> }

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'legal.privacy' })
  return { title: t('title') }
}

export default function PrivacyPolicyPage() {
  const t = useTranslations('legal.privacy')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
        </div>
        <p className="text-sm text-gray-500 mb-8">{t('lastUpdated')}</p>

        <div className="prose prose-gray max-w-none space-y-8">
          <p>{t('intro')}</p>

          <section>
            <h2>{t('controller.title')}</h2>
            <p>{t('controller.content')}</p>
          </section>

          <section>
            <h2>{t('dataCollected.title')}</h2>
            <ul>
              <li>{t('dataCollected.account')}</li>
              <li>{t('dataCollected.property')}</li>
              <li>{t('dataCollected.documents')}</li>
              <li>{t('dataCollected.photos')}</li>
              <li>{t('dataCollected.generated')}</li>
              <li>{t('dataCollected.usage')}</li>
              <li>{t('dataCollected.technical')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('purpose.title')}</h2>
            <ul>
              <li>{t('purpose.analysis')}</li>
              <li>{t('purpose.price')}</li>
              <li>{t('purpose.redesign')}</li>
              <li>{t('purpose.account')}</li>
              <li>{t('purpose.improvement')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('ai.title')}</h2>
            <p>{t('ai.content')}</p>
          </section>

          <section>
            <h2>{t('storage.title')}</h2>
            <ul>
              <li>{t('storage.structured')}</li>
              <li>{t('storage.files')}</li>
              <li>{t('storage.location')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('cookies.title')}</h2>
            <ul>
              <li>{t('cookies.essential')}</li>
              <li>{t('cookies.analytics')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('retention.title')}</h2>
            <p>{t('retention.content')}</p>
          </section>

          <section>
            <h2>{t('rights.title')}</h2>
            <p>{t('rights.content')}</p>
            <ul>
              <li>{t('rights.access')}</li>
              <li>{t('rights.rectification')}</li>
              <li>{t('rights.erasure')}</li>
              <li>{t('rights.portability')}</li>
              <li>{t('rights.objection')}</li>
            </ul>
            <p>{t('rights.contact')} <a href={`mailto:${t('contactEmail')}`} className="text-primary-600 hover:underline">{t('contactEmail')}</a></p>
          </section>

          <section>
            <h2>{t('thirdParty.title')}</h2>
            <p>{t('thirdParty.content')}</p>
            <ul>
              <li>{t('thirdParty.gcp')}</li>
              <li>{t('thirdParty.gemini')}</li>
              <li>{t('thirdParty.posthog')}</li>
              <li>{t('thirdParty.resend')}</li>
              <li>{t('thirdParty.betterAuth')}</li>
            </ul>
          </section>

          <section>
            <h2>{t('changes.title')}</h2>
            <p>{t('changes.content')}</p>
          </section>
        </div>
      </div>
    </div>
  )
}
