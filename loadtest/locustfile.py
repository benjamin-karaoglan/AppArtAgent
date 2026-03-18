"""
Load testing for AppArt Agent using Locust.

Usage:
  # Backend API only (recommended - test backend and frontend separately)
  cd ~/AppArtAgent
  LOCUST_AUTH_TOKEN="<session-cookie>" LOCUST_PROPERTY_ID=1 uv run python -m locust -f loadtest/locustfile.py --host https://api.appartagent.com

  # Frontend SSR only (separate run, different host)
  uv run python -m locust -f loadtest/locustfile.py --host https://appartagent.com FrontendUser

  # Headless mode (CI-friendly)
  LOCUST_AUTH_TOKEN="<token>" uv run python -m locust -f loadtest/locustfile.py --host https://api.appartagent.com --headless -u 50 -r 5 --run-time 2m AppArtUser

Open http://localhost:8089 for the Locust web UI when running in headed mode.

Environment variables:
  LOCUST_AUTH_TOKEN  - Better Auth session token (cookie value) for authenticated endpoints
  LOCUST_PROPERTY_ID - Property ID to use for detail/analysis tests (default: 1)
"""

import os

import urllib3
from locust import HttpUser, between, task

# Suppress SSL verification warnings (macOS Python doesn't trust system certs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

AUTH_TOKEN = os.environ.get("LOCUST_AUTH_TOKEN", "")
PROPERTY_ID = int(os.environ.get("LOCUST_PROPERTY_ID", "1"))
FRONTEND_HOST = os.environ.get("LOCUST_FRONTEND_HOST", "https://appartagent.com")


class AppArtUser(HttpUser):
    """Simulates a typical authenticated user hitting the backend API."""

    wait_time = between(1, 5)
    weight = 3

    def on_start(self):
        self.client.verify = False
        if AUTH_TOKEN:
            self.client.cookies.set("better-auth.session_token", AUTH_TOKEN)

    # -- Public endpoints (no auth needed) --

    @task(5)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(3)
    def root(self):
        self.client.get("/", name="/")

    @task(4)
    def dvf_stats(self):
        self.client.get("/api/properties/dvf-stats", name="/api/properties/dvf-stats")

    # -- Authenticated endpoints --

    @task(6)
    def list_properties(self):
        self.client.get("/api/properties/with-synthesis", name="/api/properties/with-synthesis")

    @task(3)
    def get_property_detail(self):
        self.client.get(
            f"/api/properties/{PROPERTY_ID}",
            name="/api/properties/[id]",
        )

    @task(3)
    def get_user_stats(self):
        self.client.get("/api/users/stats", name="/api/users/stats")

    @task(2)
    def get_user_me(self):
        self.client.get("/api/users/me", name="/api/users/me")

    @task(4)
    def price_analysis_summary(self):
        self.client.get(
            f"/api/properties/{PROPERTY_ID}/price-analysis",
            name="/api/properties/[id]/price-analysis",
        )

    @task(2)
    def price_analysis_full(self):
        self.client.get(
            f"/api/properties/{PROPERTY_ID}/price-analysis/full",
            name="/api/properties/[id]/price-analysis/full",
        )

    @task(2)
    def market_trend(self):
        self.client.get(
            f"/api/properties/{PROPERTY_ID}/market-trend",
            name="/api/properties/[id]/market-trend",
        )


class FrontendUser(HttpUser):
    """
    Simulates users hitting the Next.js frontend SSR pages.

    Run separately with --host https://appartagent.com:
      uv run python -m locust -f loadtest/locustfile.py --host https://appartagent.com FrontendUser
    """

    wait_time = between(2, 8)
    weight = 0  # Excluded by default (different host than API)

    def on_start(self):
        self.client.verify = False

    @task(5)
    def homepage(self):
        self.client.get("/fr", name="[frontend] /fr")

    @task(3)
    def dashboard(self):
        self.client.get("/fr/dashboard", name="[frontend] /fr/dashboard")

    @task(2)
    def properties_list(self):
        self.client.get("/fr/properties", name="[frontend] /fr/properties")

    @task(1)
    def property_detail(self):
        self.client.get(
            f"/fr/properties/{PROPERTY_ID}",
            name="[frontend] /fr/properties/[id]",
        )
