'use client'

import { useTranslations } from 'next-intl'
import { AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const t = useTranslations('errors.serverError')
  const [showDetails, setShowDetails] = useState(false)

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center max-w-md">
        <AlertTriangle className="w-16 h-16 text-danger-500 mx-auto mb-6" />
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('title')}</h1>
        <p className="text-gray-600 mb-8">{t('description')}</p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center mb-6">
          <button
            onClick={reset}
            className="px-6 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
          >
            {t('tryAgain')}
          </button>
        </div>

        {error.message && (
          <div className="text-left">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors mx-auto"
            >
              {t('details')}
              {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
            {showDetails && (
              <pre className="mt-2 p-3 bg-gray-100 rounded-lg text-xs text-gray-600 overflow-auto max-h-32">
                {error.message}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
