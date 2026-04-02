'use client'

import { useState, useEffect, useCallback } from 'react'
import { useTranslations } from 'next-intl'
import { Cookie } from 'lucide-react'

type CookiePreferences = {
  essential: boolean
  analytics: boolean
}

const COOKIE_NAME = 'cookie_consent'
const COOKIE_MAX_AGE = 365 * 24 * 60 * 60 // 12 months in seconds

function getCookieConsent(): CookiePreferences | null {
  if (typeof document === 'undefined') return null
  const match = document.cookie.match(new RegExp(`(?:^|; )${COOKIE_NAME}=([^;]*)`))
  if (!match) return null
  try {
    return JSON.parse(decodeURIComponent(match[1]))
  } catch {
    return null
  }
}

function setCookieConsent(prefs: CookiePreferences) {
  document.cookie = `${COOKIE_NAME}=${encodeURIComponent(JSON.stringify(prefs))};path=/;max-age=${COOKIE_MAX_AGE};SameSite=Lax`
  window.dispatchEvent(new CustomEvent('cookie-consent-change', { detail: prefs }))
}

export function getAnalyticsConsent(): boolean {
  const prefs = getCookieConsent()
  return prefs?.analytics ?? false
}

export default function CookieConsent() {
  const t = useTranslations('cookie')
  const [visible, setVisible] = useState(false)
  const [showPreferences, setShowPreferences] = useState(false)
  const [analyticsEnabled, setAnalyticsEnabled] = useState(false)

  useEffect(() => {
    const existing = getCookieConsent()
    if (!existing) {
      setVisible(true)
    }
  }, [])

  const handleAcceptAll = useCallback(() => {
    setCookieConsent({ essential: true, analytics: true })
    setVisible(false)
  }, [])

  const handleRejectNonEssential = useCallback(() => {
    setCookieConsent({ essential: true, analytics: false })
    setVisible(false)
  }, [])

  const handleSavePreferences = useCallback(() => {
    setCookieConsent({ essential: true, analytics: analyticsEnabled })
    setVisible(false)
  }, [analyticsEnabled])

  if (!visible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white border-t border-gray-200 shadow-lg">
      <div className="container mx-auto max-w-4xl">
        <div className="flex items-start gap-3">
          <Cookie className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900 text-sm">{t('title')}</h3>
            <p className="text-sm text-gray-600 mt-1">{t('description')}</p>

            {showPreferences && (
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('essential.title')}</p>
                    <p className="text-xs text-gray-500">{t('essential.description')}</p>
                  </div>
                  <span className="text-xs text-gray-400 font-medium">{t('alwaysActive')}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{t('analytics.title')}</p>
                    <p className="text-xs text-gray-500">{t('analytics.description')}</p>
                  </div>
                  <button
                    onClick={() => setAnalyticsEnabled(!analyticsEnabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      analyticsEnabled ? 'bg-primary-600' : 'bg-gray-300'
                    }`}
                    role="switch"
                    aria-checked={analyticsEnabled}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        analyticsEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 mt-4">
              {showPreferences ? (
                <button
                  onClick={handleSavePreferences}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  {t('savePreferences')}
                </button>
              ) : (
                <>
                  <button
                    onClick={handleAcceptAll}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    {t('acceptAll')}
                  </button>
                  <button
                    onClick={handleRejectNonEssential}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    {t('rejectNonEssential')}
                  </button>
                  <button
                    onClick={() => setShowPreferences(true)}
                    className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    {t('managePreferences')}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
