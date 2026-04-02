'use client'

import { useState, useRef } from 'react'
import { useTranslations } from 'next-intl'
import { X, Upload, CheckCircle } from 'lucide-react'
import { feedbackAPI } from '@/lib/api'

type FeedbackType = 'bug_report' | 'feature_request' | 'general_feedback'

interface FeedbackModalProps {
  isOpen: boolean
  onClose: () => void
  defaultType?: FeedbackType
}

export default function FeedbackModal({ isOpen, onClose, defaultType }: FeedbackModalProps) {
  const t = useTranslations('feedback')
  const [type, setType] = useState<FeedbackType>(defaultType ?? 'general_feedback')
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [screenshot, setScreenshot] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(false)

    try {
      await feedbackAPI.submit({
        type,
        message,
        email: email || undefined,
        screenshot: screenshot ?? undefined,
      })
      setSuccess(true)
      setTimeout(() => {
        onClose()
        // Reset form
        setType('general_feedback')
        setMessage('')
        setEmail('')
        setScreenshot(null)
        setSuccess(false)
      }, 2000)
    } catch {
      setError(true)
    } finally {
      setSubmitting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.size <= 5 * 1024 * 1024) {
      setScreenshot(file)
    }
  }

  const types: FeedbackType[] = ['bug_report', 'feature_request', 'general_feedback']

  return (
    <div className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-t-xl sm:rounded-xl shadow-xl w-full sm:max-w-md max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">{t('title')}</h2>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {success ? (
          <div className="p-8 text-center">
            <CheckCircle className="w-12 h-12 text-success-500 mx-auto mb-3" />
            <p className="text-gray-700">{t('success')}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('type.label')}</label>
              <div className="flex gap-2">
                {types.map((feedbackType) => (
                  <button
                    key={feedbackType}
                    type="button"
                    onClick={() => setType(feedbackType)}
                    className={`flex-1 px-3 py-2 text-xs font-medium rounded-lg border transition-colors ${
                      type === feedbackType
                        ? 'bg-primary-50 border-primary-300 text-primary-700'
                        : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {t(`type.${feedbackType}`)}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('message.label')}</label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={t('message.placeholder')}
                rows={4}
                required
                minLength={10}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('email.label')}</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={t('email.placeholder')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('screenshot.label')}</label>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 px-3 py-3 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors"
              >
                <Upload className="w-4 h-4" />
                {screenshot ? screenshot.name : t('screenshot.hint')}
              </button>
            </div>

            {error && (
              <p className="text-sm text-danger-600">{t('error')}</p>
            )}

            <button
              type="submit"
              disabled={submitting || message.length < 10}
              className="w-full px-4 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? t('submitting') : t('submit')}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
