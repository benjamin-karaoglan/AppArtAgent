import posthog from 'posthog-js'

export const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN ?? ''
export const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? 'https://eu.i.posthog.com'

export const POSTHOG_CONFIG = {
  api_host: '/ingest',
  ui_host: POSTHOG_HOST,
  person_profiles: 'identified_only' as const,
  capture_pageview: false,
  capture_pageleave: true,
  autocapture: true,
}

export default posthog
