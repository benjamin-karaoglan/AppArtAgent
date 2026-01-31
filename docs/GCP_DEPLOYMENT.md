# GCP Deployment Guide

This guide covers deploying AppArt Agent to Google Cloud Platform.

## Architecture Overview

```
                            ┌──────────────────────────┐
                            │   appartagent.com (DNS)  │
                            │   ├── appartagent.com    │──┐
                            │   ├── www.appartagent.com│──┤
                            │   └── api.appartagent.com│──┼───┐
                            └──────────────────────────┘  │   │
                                                          │   │
┌─────────────────────────────────────────────────────────┼───┼───────────────┐
│                           Google Cloud Platform         │   │               │
│                                                         │   │               │
│  ┌─────────────────────────────────────────────────────┼───┼─────────────┐ │
│  │                    Cloud Run Domain Mapping          │   │             │ │
│  │                    (Managed SSL Certificates)        │   │             │ │
│  └─────────────────────────────────────────────────────┼───┼─────────────┘ │
│                                                         │   │               │
│  ┌─────────────┐                               ┌───────┴───┴─────┐         │
│  │   Cloud     │◀──────────────────────────────│     Cloud       │         │
│  │   Run       │                               │     Run         │         │
│  │  Frontend   │──────────────────────────────▶│    Backend      │         │
│  └─────────────┘                               └───────┬─────────┘         │
│                                                        │                    │
│         ┌──────────────────────────────────────────────┤                   │
│         │                    │                         │                    │
│         ▼                    ▼                         ▼                    │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐          │
│  │   Cloud     │     │  Cloud SQL  │     │ Memorystore Redis   │          │
│  │  Storage    │     │ PostgreSQL  │     │                     │          │
│  │  (GCS)      │     │             │     │                     │          │
│  └─────────────┘     └─────────────┘     └─────────────────────┘          │
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │  Secret     │     │  Artifact   │     │  Vertex AI  │                  │
│  │  Manager    │     │  Registry   │     │   (Gemini)  │                  │
│  └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐          │
│  │  Cloud DNS (Optional - can use external DNS)                 │          │
│  │  ├── A record: appartagent.com → Cloud Run IPs               │          │
│  │  ├── CNAME: www.appartagent.com → ghs.googlehosted.com       │          │
│  │  └── CNAME: api.appartagent.com → ghs.googlehosted.com       │          │
│  └─────────────────────────────────────────────────────────────┘          │
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
cd appart-agent

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
  aiplatform.googleapis.com \
  dns.googleapis.com
```

### 3. Create Service Account for CI/CD

```bash
# Create service account
gcloud iam service-accounts create appart-deployer \
  --display-name="AppArt Agent Deployer"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appart-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appart-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appart-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appart-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:appart-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create deployer-key.json \
  --iam-account=appart-deployer@$PROJECT_ID.iam.gserviceaccount.com

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
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/appart-agent/backend:latest \
  --target production .
docker push $REGION-docker.pkg.dev/$PROJECT_ID/appart-agent/backend:latest

# Build and push frontend
cd ../frontend
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/appart-agent/frontend:latest \
  --target production -f Dockerfile.pnpm .
docker push $REGION-docker.pkg.dev/$PROJECT_ID/appart-agent/frontend:latest

# Deploy to Cloud Run
gcloud run deploy appart-backend \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/appart-agent/backend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

gcloud run deploy appart-frontend \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/appart-agent/frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated
```

## Database Migrations

Run migrations after deployment:

```bash
# Connect to Cloud SQL via Cloud Run job
gcloud run jobs create db-migrate \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/appart-agent/backend:latest \
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

The infrastructure supports custom domain configuration via Terraform. This sets up:
- `appartagent.com` → Frontend
- `www.appartagent.com` → Frontend
- `api.appartagent.com` → Backend API

### Option 1: Using Terraform (Recommended)

#### Step 1: Verify Domain Ownership

Before Cloud Run can serve your domain, you must verify ownership:

```bash
# Option A: Using gcloud (opens browser for verification)
gcloud domains verify appartagent.com

# Option B: Via Google Search Console
# Visit: https://search.google.com/search-console
# Add property → Domain → appartagent.com
# Follow DNS TXT record verification
```

#### Step 2: Configure Terraform Variables

Update your `terraform.tfvars`:

```hcl
# Custom domain configuration
domain = "appartagent.com"
create_dns_zone = true  # Terraform manages DNS
api_subdomain = "api"   # Results in api.appartagent.com
```

#### Step 3: Apply Infrastructure

```bash
cd infra/terraform
terraform plan   # Review changes
terraform apply  # Apply changes
```

#### Step 4: Update Domain Registrar Nameservers

After applying, Terraform outputs the Cloud DNS nameservers. Update your domain registrar (where you bought appartagent.com) to use these nameservers:

```bash
# Get the nameservers
terraform output dns_nameservers
```

You'll see output like:
```
dns_nameservers = [
  "ns-cloud-a1.googledomains.com.",
  "ns-cloud-a2.googledomains.com.",
  "ns-cloud-a3.googledomains.com.",
  "ns-cloud-a4.googledomains.com.",
]
```

Go to your domain registrar and set these as the authoritative nameservers.

#### Step 5: Wait for DNS Propagation & SSL

- DNS propagation: 5 minutes to 48 hours (usually ~1 hour)
- SSL certificate provisioning: 15-60 minutes after DNS is verified

Check domain mapping status:
```bash
gcloud run domain-mappings describe \
  --domain appartagent.com \
  --region europe-west1
```

### Option 2: External DNS (Managing DNS Outside GCP)

If you prefer to manage DNS at your registrar (e.g., Cloudflare, Namecheap):

```hcl
# terraform.tfvars
domain = "appartagent.com"
create_dns_zone = false  # Don't create Cloud DNS zone
```

Then configure these DNS records at your registrar:

| Type | Name | Value |
|------|------|-------|
| A | appartagent.com | (see domain mapping for IP) |
| CNAME | www | ghs.googlehosted.com. |
| CNAME | api | ghs.googlehosted.com. |

Get the required A record IP addresses:
```bash
gcloud run domain-mappings describe \
  --domain appartagent.com \
  --region europe-west1 \
  --format='value(status.resourceRecords)'
```

### Manual Domain Setup (Without Terraform)

If you need to set up domains manually:

```bash
# Verify domain
gcloud domains verify appartagent.com

# Create domain mappings
gcloud run domain-mappings create \
  --service appart-frontend \
  --domain appartagent.com \
  --region europe-west1

gcloud run domain-mappings create \
  --service appart-frontend \
  --domain www.appartagent.com \
  --region europe-west1

gcloud run domain-mappings create \
  --service appart-backend \
  --domain api.appartagent.com \
  --region europe-west1

# List domain mappings to get DNS records
gcloud run domain-mappings list --region europe-west1
```

### Troubleshooting Custom Domain

**Domain mapping stuck in "pending":**
```bash
# Check status
gcloud run domain-mappings describe --domain appartagent.com --region europe-west1

# Common issues:
# - Domain not verified: Run `gcloud domains verify appartagent.com`
# - DNS not propagated: Wait and check with `dig appartagent.com`
# - Wrong DNS records: Verify A/CNAME records are correct
```

**SSL certificate not provisioning:**
- Ensure DNS records are correctly pointing to Cloud Run
- Check certificate status in Cloud Console → Cloud Run → Domain mappings
- Can take up to 24 hours in some cases

**Test DNS propagation:**
```bash
# Check A record
dig appartagent.com A

# Check CNAME
dig www.appartagent.com CNAME
dig api.appartagent.com CNAME
```

## Monitoring & Logging

### View Logs

```bash
# Backend logs
gcloud run services logs read appart-backend --region $REGION

# Frontend logs
gcloud run services logs read appart-frontend --region $REGION

# Real-time logs
gcloud run services logs tail appart-backend --region $REGION
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
gcloud run services logs read appart-backend --region $REGION --limit 100
```

### Database connection issues

Verify VPC connector is working:
```bash
gcloud compute networks vpc-access connectors describe \
  appart-agent-connector --region $REGION
```

### Redis connection issues

Check Redis instance is running:
```bash
gcloud redis instances describe appart-agent-cache --region $REGION
```

## Cleanup

To destroy all resources:

```bash
cd infra/terraform
terraform destroy
```

⚠️ This will delete all data including the database!
