# Prerequisites

## Required for All Users

### Docker and Docker Compose

Docker is required to run the full application stack.

=== "macOS"
    ```bash
    # Install Docker Desktop
    brew install --cask docker
    
    # Or download from https://www.docker.com/products/docker-desktop
    ```

=== "Linux"
    ```bash
    # Install Docker
    curl -fsSL https://get.docker.com | sh
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Install Docker Compose
    sudo apt install docker-compose-plugin
    ```

=== "Windows"
    Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop).

Verify installation:

```bash
docker --version
docker compose version
```

### API Keys

#### Google Cloud API Key (Recommended)

Used for Gemini AI services (document analysis, image generation).

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API key"
3. Create a new project or select existing
4. Copy the API key

#### Anthropic API Key (Legacy)

If you prefer Claude over Gemini:

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Navigate to API Keys
3. Create a new key

!!! note
    The application defaults to Gemini. Anthropic support is maintained for backward compatibility.

## Required for Local Development

If you want to run services without Docker:

### Python 3.10+

=== "macOS"
    ```bash
    brew install python@3.11
    ```

=== "Linux"
    ```bash
    sudo apt install python3.11 python3.11-venv
    ```

=== "Windows"
    Download from [python.org](https://www.python.org/downloads/)

### UV (Python Package Manager)

UV provides 75x faster package installation than pip.

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

### Node.js 18+

=== "macOS"
    ```bash
    brew install node@20
    ```

=== "Linux"
    ```bash
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install nodejs
    ```

=== "Windows"
    Download from [nodejs.org](https://nodejs.org/)

### pnpm (JavaScript Package Manager)

pnpm provides 5-10x faster installs than npm.

```bash
# Install pnpm
npm install -g pnpm

# Verify
pnpm --version
```

## Optional Tools

### PostgreSQL Client

For direct database access:

=== "macOS"
    ```bash
    brew install postgresql
    ```

=== "Linux"
    ```bash
    sudo apt install postgresql-client
    ```

### Graphviz

For generating workflow diagrams:

=== "macOS"
    ```bash
    brew install graphviz
    ```

=== "Linux"
    ```bash
    sudo apt install graphviz graphviz-dev
    ```

### Terraform

For GCP infrastructure deployment:

```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform

# Verify
terraform --version
```

### Google Cloud CLI

For GCP deployment and management:

```bash
# macOS
brew install --cask google-cloud-sdk

# Initialize
gcloud init
```

## Development Environment

### Recommended VS Code Extensions

- Python (Microsoft)
- Pylance
- ESLint
- Tailwind CSS IntelliSense
- Docker
- GitLens

### Recommended Settings

Create `.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.formatting.provider": "black",
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000
}
```

## Verification Checklist

Run these commands to verify your setup:

```bash
# Docker
docker --version          # Should show Docker version
docker compose version    # Should show Compose version

# Python (for local dev)
python3 --version         # Should show 3.10+
uv --version              # Should show UV version

# Node.js (for local dev)
node --version            # Should show 18+
pnpm --version            # Should show pnpm version
```
