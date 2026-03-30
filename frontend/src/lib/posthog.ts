import posthog from 'posthog-js'

export const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN ?? ''
export const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? 'https://eu.i.posthog.com'

export function initPostHog() {
  if (typeof window === 'undefined' || !POSTHOG_KEY) return

  posthog.init(POSTHOG_KEY, {
    api_host: '/ingest',
    ui_host: POSTHOG_HOST,
    person_profiles: 'identified_only',
    capture_pageview: false, // We handle this manually with the Next.js router
    capture_pageleave: true,
    autocapture: true,
  })
}

export default posthog
