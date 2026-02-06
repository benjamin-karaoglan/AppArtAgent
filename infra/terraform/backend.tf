# =============================================================================
# Terraform Remote State Backend (GCS)
# =============================================================================
#
# State is stored in a GCS bucket for team collaboration. The bucket name
# is provided via a partial configuration file (backend.hcl) to avoid
# hardcoding project-specific values.
#
# Setup (first time):
#   1. Run: ./scripts/setup-remote-state.sh <PROJECT_ID> [REGION]
#   2. Run: terraform init -backend-config=backend.hcl -migrate-state
#
# Setup (joining an existing team):
#   1. Copy backend.hcl.example to backend.hcl
#   2. Fill in your project's bucket name
#   3. Run: terraform init -backend-config=backend.hcl
#
# =============================================================================

terraform {
  backend "gcs" {
    # Configured via -backend-config=backend.hcl
    # See backend.hcl.example for the template
  }
}
