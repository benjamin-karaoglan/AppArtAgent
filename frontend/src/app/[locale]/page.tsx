"use client";

import { Link } from '@/i18n/navigation'
import { useTranslations } from 'next-intl'
import { FileText, Image as ImageIcon, TrendingUp, Shield, Calculator } from 'lucide-react'
import Header from '@/components/Header'
import AppArtLogo from '@/components/AppArtLogo'
import { useAuth } from '@/contexts/AuthContext'

export default function HomePage() {
  const t = useTranslations('home')
  const { isAuthenticated, loading } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
      <Header />
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            {t('hero.title')}
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            {t('hero.subtitle')}
          </p>
          <div className="flex gap-4 justify-center">
            {!loading && isAuthenticated ? (
              <>
                <Link href="/dashboard" className="btn-primary text-lg px-8 py-3 text-center min-w-[11.5rem]">
                  {t('hero.goToDashboard')}
                </Link>
                <Link href="/properties" className="btn-secondary text-lg px-8 py-3 text-center min-w-[11.5rem]">
                  {t('hero.viewProperties')}
                </Link>
              </>
            ) : (
              <>
                <Link href="/auth/register" className="btn-primary text-lg px-8 py-3 text-center min-w-[11.5rem]">
                  {t('hero.getStarted')}
                </Link>
                <Link href="/auth/login" className="btn-secondary text-lg px-8 py-3 text-center min-w-[11.5rem]">
                  {t('hero.signIn')}
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16">
          <FeatureCard
            icon={<TrendingUp className="w-12 h-12 text-primary-600" />}
            title={t('features.priceAnalysis.title')}
            description={t('features.priceAnalysis.description')}
          />
          <FeatureCard
            icon={<FileText className="w-12 h-12 text-primary-600" />}
            title={t('features.documentAnalysis.title')}
            description={t('features.documentAnalysis.description')}
          />
          <FeatureCard
            icon={<Shield className="w-12 h-12 text-primary-600" />}
            title={t('features.riskAssessment.title')}
            description={t('features.riskAssessment.description')}
          />
          <FeatureCard
            icon={<Calculator className="w-12 h-12 text-primary-600" />}
            title={t('features.costCalculator.title')}
            description={t('features.costCalculator.description')}
          />
          <FeatureCard
            icon={<ImageIcon className="w-12 h-12 text-primary-600" />}
            title={t('features.styleVisualization.title')}
            description={t('features.styleVisualization.description')}
          />
          <FeatureCard
            icon={<AppArtLogo size={48} className="text-primary-600" />}
            title={t('features.investmentScore.title')}
            description={t('features.investmentScore.description')}
          />
        </div>

        {/* How It Works */}
        <div className="mt-24">
          <h2 className="text-3xl font-bold text-center mb-12">{t('howItWorks.title')}</h2>
          <div className="grid md:grid-cols-4 gap-8">
            <Step number="1" title={t('howItWorks.step1.title')} description={t('howItWorks.step1.description')} />
            <Step number="2" title={t('howItWorks.step2.title')} description={t('howItWorks.step2.description')} />
            <Step number="3" title={t('howItWorks.step3.title')} description={t('howItWorks.step3.description')} />
            <Step number="4" title={t('howItWorks.step4.title')} description={t('howItWorks.step4.description')} />
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-24 text-center bg-primary-600 text-white rounded-2xl p-12">
          <h2 className="text-3xl font-bold mb-4">{t('cta.title')}</h2>
          <p className="text-xl mb-8 opacity-90">{t('cta.subtitle')}</p>
          {!loading && isAuthenticated ? (
            <Link href="/dashboard" className="bg-white text-primary-600 hover:bg-gray-100 font-medium py-3 px-8 rounded-lg transition-colors inline-block">
              {t('cta.goToDashboard')}
            </Link>
          ) : (
            <Link href="/auth/register" className="bg-white text-primary-600 hover:bg-gray-100 font-medium py-3 px-8 rounded-lg transition-colors inline-block">
              {t('cta.button')}
            </Link>
          )}
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-8 mt-16">
        <div className="container mx-auto px-4 text-center">
          <p>{t('footer.copyright')}</p>
          <p className="text-gray-400 mt-2">{t('footer.tagline')}</p>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function Step({ number, title, description }: { number: string, title: string, description: string }) {
  return (
    <div className="text-center">
      <div className="w-16 h-16 bg-primary-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
        {number}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}
