# Deployment

This section covers deploying Appartment Agent to various environments.

## Deployment Options

| Option | Best For | Complexity |
|--------|----------|------------|
| [Docker](docker.md) | Local development, self-hosted | Low |
| [GCP Cloud Run](gcp.md) | Production, scalable | Medium |

## Environment Comparison

| Feature | Docker (Local) | GCP Cloud Run |
|---------|---------------|---------------|
| **Database** | PostgreSQL container | Cloud SQL |
| **Storage** | MinIO | Cloud Storage |
| **Cache** | Redis container | Memorystore |
| **AI** | Gemini API | Vertex AI |
| **Cost** | Free | ~$50-150/month |
| **Scaling** | Manual | Automatic |

## Quick Reference

### Docker Deployment

```bash
# Build and start
docker-compose up -d --build

# Run migrations
docker-compose exec backend alembic upgrade head

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### GCP Deployment

```bash
# Initialize Terraform
cd infra/terraform
terraform init

# Apply infrastructure
terraform apply

# Deploy via GitHub Actions (automatic on push to main)
git push origin main
```

## Prerequisites

### Docker

- Docker Engine 20.10+
- Docker Compose v2
- 4GB+ RAM available
- 10GB+ disk space

### GCP

- GCP project with billing enabled
- gcloud CLI authenticated
- Terraform 1.5+
- GitHub repository with Actions enabled
