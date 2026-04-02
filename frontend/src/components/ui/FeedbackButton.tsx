'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { MessageSquarePlus } from 'lucide-react'
import FeedbackModal from './FeedbackModal'

export default function FeedbackButton() {
  const t = useTranslations('feedback')
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-40 flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-primary-600 rounded-full shadow-lg hover:bg-primary-700 transition-all hover:shadow-xl"
        aria-label={t('button')}
      >
        <MessageSquarePlus className="w-4 h-4" />
        <span className="hidden sm:inline">{t('button')}</span>
      </button>
      <FeedbackModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  )
}
