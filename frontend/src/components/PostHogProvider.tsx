'use client'

import { Suspense, useEffect, useState } from 'react'
import { usePathname, useSearchParams } from 'next/navigation'
import posthog from 'posthog-js'
import { PostHogProvider as PHProvider } from 'posthog-js/react'
import { POSTHOG_KEY, POSTHOG_HOST } from '@/lib/posthog'
import { getAnalyticsConsent } from '@/components/ui/CookieConsent'

function PostHogPageView() {
  const pathname = usePathname()
  const searchParams = useSearchParams()

  useEffect(() => {
    if (!POSTHOG_KEY) return
    const url = window.origin + pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '')
    posthog.capture('$pageview', { $current_url: url })
  }, [pathname, searchParams])

  return null
}

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  const [analyticsAllowed, setAnalyticsAllowed] = useState(false)

  useEffect(() => {
    // Check initial consent
    setAnalyticsAllowed(getAnalyticsConsent())

    // Listen for consent changes
    const handleConsentChange = (e: Event) => {
      const detail = (e as CustomEvent).detail
      setAnalyticsAllowed(detail.analytics)

      if (detail.analytics && POSTHOG_KEY) {
        posthog.init(POSTHOG_KEY, {
          api_host: '/ingest',
          ui_host: POSTHOG_HOST,
          person_profiles: 'identified_only',
          capture_pageview: false,
          capture_pageleave: true,
          autocapture: true,
        })
      } else if (!detail.analytics && posthog.__loaded) {
        posthog.opt_out_capturing()
      }
    }

    window.addEventListener('cookie-consent-change', handleConsentChange)
    return () => window.removeEventListener('cookie-consent-change', handleConsentChange)
  }, [])

  // Initialize PostHog if consent was already given (returning user)
  useEffect(() => {
    if (analyticsAllowed && POSTHOG_KEY && !posthog.__loaded) {
      posthog.init(POSTHOG_KEY, {
        api_host: '/ingest',
        ui_host: POSTHOG_HOST,
        person_profiles: 'identified_only',
        capture_pageview: false,
        capture_pageleave: true,
        autocapture: true,
      })
    }
  }, [analyticsAllowed])

  if (!POSTHOG_KEY || !analyticsAllowed) {
    return <>{children}</>
  }

  return (
    <PHProvider client={posthog}>
      <Suspense fallback={null}>
        <PostHogPageView />
      </Suspense>
      {children}
    </PHProvider>
  )
}
