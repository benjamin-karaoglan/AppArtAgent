# GCP Deployment Guide

This guide covers deploying Appartment Agent to Google Cloud Platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Google Cloud Platform                              │
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐                                       │
│  │   Cloud     │     │   Cloud     │                                       │
│  │   Run       │────▶│   Run       │                                       │
│  │  Frontend   │     │  Backend    │                                       │
│  └─────────────┘     └──────┬──────┘                                       │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                          │
│         │                   │                   │                          │
│         ▼                   ▼                   ▼                          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │   Cloud     │     │  Cloud SQL  │     │ Memorystore │                  │
│  │  Storage    │     │ PostgreSQL  │     │   Redis     │                  │
│  │  (GCS)      │     │             │     │             │                  │
│  └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │  Secret     │     │  Artifact   │     │  Vertex AI  │                  │
│  │  Manager    │     │  Registry   │     │   (Gemini)  │                  │
│  └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Terraform** >= 1.5.0 installed
4. **Domain** (optional, for custom domain)

## Cost Estimation

| Service | Tier | Estimated Monthly Cost |
|---------|------|----------------------|
| Cloud Run (Frontend) | 0-10 instances | $0-50 |
| Cloud Run (Backend) | 0-10 instances | $0-100 |
| Cloud SQL PostgreSQL | db-f1-micro | ~$10 |
| Cloud SQL PostgreSQL | db-custom-2-4096 (prod) | ~$50 |
| Memorystore Redis | BASIC 1GB | ~$35 |
| Cloud Storage | ~10GB | ~$0.50 |
| **Total (Dev)** | | **~$50/month** |
| **Total (Production)** | | **~$150/month** |

## Quick Start

### 1. Initial Setup

```bash
# Clone and navigate
cd appartment-agent

# Set your GCP project
export PROJECT_ID="your-project-id"
export REGION="europe-west1"

# Authenticate
gcloud auth login
gcloud config set project $PROJECT_ID
```

### 2. Enable APIs

```bash
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
  aiplatform.googleapis.com
```

### 3. Create Service Account for CI/CD

```bash
# Create service account
gcloud iam service-accounts create appartment-deployer \
  --display-name="Appartment Agent Deployer"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appartment-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appartment-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appartment-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appartment-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appartment-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create deployer-key.json \
  --iam-account=appartment-deployer@$PROJECT_ID.iam.gserviceaccount.com

echo "Add this as GCP_SA_KEY secret in GitHub"
cat deployer-key.json | base64
```

### 4. Deploy with Terraform

```bash
cd infra/terraform

# Copy and edit variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project ID

# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply (creates all infrastructure)
terraform apply
```

### 5. Configure GitHub Secrets

Add these secrets to your GitHub repository:

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | Your GCP project ID |
| `GCP_REGION` | GCP region (e.g., `europe-west1`) |
| `GCP_SA_KEY` | Service account key JSON (base64 encoded) |

### 6. Set Google Cloud API Key

The Gemini API key needs to be set manually in Secret Manager:

```bash
# Create the secret with your API key
echo -n "your-google-cloud-api-key" | \
  gcloud secrets create google-cloud-api-key \
  --data-file=-

# Or update existing
echo -n "your-google-cloud-api-key" | \
  gcloud secrets versions add google-cloud-api-key \
  --data-file=-
```

### 7. Deploy

Push to main branch to trigger deployment:

```bash
git push origin main
```

## Manual Deployment

If not using GitHub Actions:

```bash
# Build and push backend
cd backend
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/appartment-agent/backend:latest \
  --target production .
docker push $REGION-docker.pkg.dev/$PROJECT_ID/appartment-agent/backend:latest

# Build and push frontend
cd ../frontend
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/appartment-agent/frontend:latest \
  --target production -f Dockerfile.pnpm .
docker push $REGION-docker.pkg.dev/$PROJECT_ID/appartment-agent/frontend:latest

# Deploy to Cloud Run
gcloud run deploy appartment-backend \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/appartment-agent/backend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

gcloud run deploy appartment-frontend \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/appartment-agent/frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated
```

## Database Migrations

Run migrations after deployment:

```bash
# Connect to Cloud SQL via Cloud Run job
gcloud run jobs create db-migrate \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/appartment-agent/backend:latest \
  --region $REGION \
  --memory 1Gi \
  --command "alembic" \
  --args "upgrade,head"

gcloud run jobs execute db-migrate --region $REGION --wait
```

## Environment Variables

### Backend (Cloud Run)

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | `production` | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes (from Secret Manager) |
| `SECRET_KEY` | JWT signing key | Yes (from Secret Manager) |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Yes |
| `GOOGLE_CLOUD_LOCATION` | GCP region | Yes |
| `GEMINI_USE_VERTEXAI` | `true` for Vertex AI | Yes |
| `STORAGE_BACKEND` | `gcs` | Yes |
| `GCS_DOCUMENTS_BUCKET` | Documents bucket name | Yes |
| `GCS_PHOTOS_BUCKET` | Photos bucket name | Yes |
| `REDIS_HOST` | Redis IP address | Yes |
| `REDIS_PORT` | Redis port (6379) | Yes |

### Frontend (Cloud Run)

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend URL | Yes |
| `NODE_ENV` | `production` | Yes |

## Custom Domain Setup

1. **Verify domain** in GCP:
   ```bash
   gcloud domains verify your-domain.com
   ```

2. **Map domain** to Cloud Run:
   ```bash
   gcloud run domain-mappings create \
     --service appartment-frontend \
     --domain app.your-domain.com \
     --region $REGION
   ```

3. **Update DNS** with the provided records

## Monitoring & Logging

### View Logs

```bash
# Backend logs
gcloud run services logs read appartment-backend --region $REGION

# Frontend logs
gcloud run services logs read appartment-frontend --region $REGION

# Real-time logs
gcloud run services logs tail appartment-backend --region $REGION
```

### Cloud Monitoring

Set up alerts in Cloud Monitoring for:
- Error rate > 1%
- Latency p95 > 2s
- Instance count at max

## Scaling Configuration

### Auto-scaling

Cloud Run automatically scales based on traffic. Configure in Terraform:

```hcl
scaling {
  min_instance_count = 1  # Keep warm for production
  max_instance_count = 10 # Max instances
}
```

### Cold Start Optimization

- Set `min_instance_count = 1` for production to avoid cold starts
- Use smaller container images
- Optimize startup time in application

## Security Considerations

1. **VPC Connector** ensures Cloud Run can access private Cloud SQL and Redis
2. **Secret Manager** stores sensitive values (DB password, JWT secret)
3. **IAM** limits service account permissions
4. **Private IP** for Cloud SQL (no public IP)
5. **Automatic HTTPS** on Cloud Run

## Troubleshooting

### Container won't start

Check logs:
```bash
gcloud run services logs read appartment-backend --region $REGION --limit 100
```

### Database connection issues

Verify VPC connector is working:
```bash
gcloud compute networks vpc-access connectors describe \
  appartment-agent-connector --region $REGION
```

### Redis connection issues

Check Redis instance is running:
```bash
gcloud redis instances describe appartment-agent-cache --region $REGION
```

## Cleanup

To destroy all resources:

```bash
cd infra/terraform
terraform destroy
```

⚠️ This will delete all data including the database!
