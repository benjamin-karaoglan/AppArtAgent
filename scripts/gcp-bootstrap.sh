#!/bin/bash
# =============================================================================
# GCP Bootstrap Script
# =============================================================================
# This script sets up the initial GCP infrastructure for AppArt Agent.
# Run this once to prepare your GCP project for deployment.
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  AppArt Agent - GCP Bootstrap   ${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Check prerequisites
command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}gcloud CLI is required but not installed. Aborting.${NC}"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo -e "${RED}Terraform is required but not installed. Aborting.${NC}"; exit 1; }

# Get project ID
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Enter your GCP Project ID:${NC}"
    read -r PROJECT_ID
fi

# Get region
REGION=${REGION:-"europe-west1"}
echo -e "${YELLOW}Using region: ${REGION} (set REGION env var to change)${NC}"

echo ""
echo -e "${GREEN}Project ID: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Region: ${REGION}${NC}"
echo ""

# Confirm
echo -e "${YELLOW}Continue with this configuration? (y/n)${NC}"
read -r confirm
if [ "$confirm" != "y" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${GREEN}Step 1: Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    vpcaccess.googleapis.com \
    servicenetworking.googleapis.com \
    compute.googleapis.com \
    aiplatform.googleapis.com \
    --project "$PROJECT_ID"

echo ""
echo -e "${GREEN}Step 2: Creating Artifact Registry repository...${NC}"
gcloud artifacts repositories create appart-agent \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker images for AppArt Agent" \
    --project "$PROJECT_ID" 2>/dev/null || echo "Repository already exists"

echo ""
echo -e "${GREEN}Step 3: Creating deployment service account...${NC}"
SA_NAME="appart-deployer"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam service-accounts create "$SA_NAME" \
    --display-name="AppArt Agent Deployer" \
    --project "$PROJECT_ID" 2>/dev/null || echo "Service account already exists"

# Grant permissions
for role in "roles/run.admin" "roles/iam.serviceAccountUser" "roles/artifactregistry.writer" \
    "roles/secretmanager.secretAccessor" "roles/storage.admin" "roles/cloudsql.client"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$role" \
        --quiet
done

echo ""
echo -e "${GREEN}Step 4: Creating service account key...${NC}"
KEY_FILE="deployer-key.json"
if [ ! -f "$KEY_FILE" ]; then
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL" \
        --project "$PROJECT_ID"
    echo -e "${GREEN}Key saved to ${KEY_FILE}${NC}"
else
    echo -e "${YELLOW}Key file already exists. Skipping.${NC}"
fi

echo ""
echo -e "${GREEN}Step 5: Setting up Terraform...${NC}"
cd "$(dirname "$0")/../infra/terraform"

# Create terraform.tfvars
cat > terraform.tfvars << EOF
project_id = "$PROJECT_ID"
region     = "$REGION"
environment = "production"
EOF

echo "Created terraform.tfvars"

echo ""
echo -e "${GREEN}Step 6: Initializing Terraform...${NC}"
terraform init

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Bootstrap Complete!                ${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Review the Terraform plan:"
echo "   cd infra/terraform && terraform plan"
echo ""
echo "2. Apply Terraform (creates infrastructure):"
echo "   terraform apply"
echo ""
echo "3. Add GitHub secrets:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_REGION: $REGION"
echo "   - GCP_SA_KEY: $(cat "$KEY_FILE" | base64 | tr -d '\n')"
echo ""
echo "4. Set your Google Cloud API key in Secret Manager:"
echo "   echo -n 'your-api-key' | gcloud secrets create google-cloud-api-key --data-file=-"
echo ""
echo "5. Push to main branch to trigger deployment:"
echo "   git push origin main"
echo ""
