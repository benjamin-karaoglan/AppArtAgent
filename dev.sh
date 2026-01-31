#!/bin/bash
# Development helper script with hot-reload support

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to check if containers are running
check_running() {
    docker-compose ps --services --filter "status=running" | grep -q "$1"
}

# Function to start services with hot-reload
start() {
    print_header "Starting Development Environment with Hot-Reload"

    print_info "Starting all services..."
    docker-compose up -d

    print_info "Waiting for services to be healthy..."
    sleep 5

    if check_running "backend"; then
        print_success "Backend running at http://localhost:8000"
        print_info "  API Docs: http://localhost:8000/docs"
        print_info "  Hot-reload: Enabled (Uvicorn --reload)"
        print_info "  Storage: MinIO (local)"
    else
        print_error "Backend failed to start"
    fi

    if check_running "frontend"; then
        print_success "Frontend running at http://localhost:3000"
        print_info "  Hot-reload: Enabled (Next.js Fast Refresh)"
    else
        print_error "Frontend failed to start"
    fi

    if check_running "db"; then
        print_success "PostgreSQL running at localhost:5432"
    else
        print_error "Database failed to start"
    fi

    if check_running "redis"; then
        print_success "Redis running at localhost:6379"
    else
        print_error "Redis failed to start"
    fi

    if check_running "minio"; then
        print_success "MinIO running at localhost:9000"
        print_info "  Console: http://localhost:9001"
    else
        print_error "MinIO failed to start"
    fi

    echo ""
    print_header "Hot-Reload is Active!"
    echo "Edit your code and watch it reload automatically:"
    echo "  • Backend (Python): ~1 second restart"
    echo "  • Frontend (React): Instant HMR"
    echo ""
    echo "View logs with: ./dev.sh logs"
}

# Function to start services with GCS (Google Cloud Storage) instead of MinIO
start_gcs() {
    print_header "Starting Development Environment with GCS"

    # Check required environment variables
    if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
        print_error "GOOGLE_CLOUD_PROJECT environment variable is required"
        echo "  export GOOGLE_CLOUD_PROJECT=your-project-id"
        exit 1
    fi

    if [ -z "$GCS_DOCUMENTS_BUCKET" ]; then
        print_info "GCS_DOCUMENTS_BUCKET not set, will use default: \${GOOGLE_CLOUD_PROJECT}-documents"
    fi

    # Check for Google Cloud credentials
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        if [ -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
            export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/application_default_credentials.json"
            print_info "Using ADC from: $GOOGLE_APPLICATION_CREDENTIALS"
        else
            print_error "Google Cloud credentials not found"
            echo "  Run: gcloud auth application-default login"
            echo "  Or set: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json"
            exit 1
        fi
    else
        print_info "Using credentials from: $GOOGLE_APPLICATION_CREDENTIALS"
    fi

    print_info "Starting services with GCS backend..."
    docker-compose -f docker-compose.yml -f docker-compose.gcs.yml up -d backend frontend db redis

    print_info "Waiting for services to be healthy..."
    sleep 5

    if check_running "backend"; then
        print_success "Backend running at http://localhost:8000"
        print_info "  API Docs: http://localhost:8000/docs"
        print_info "  Hot-reload: Enabled (Uvicorn --reload)"
        print_info "  Storage: Google Cloud Storage"
        print_info "  Documents bucket: ${GCS_DOCUMENTS_BUCKET:-${GOOGLE_CLOUD_PROJECT}-documents}"
        print_info "  Photos bucket: ${GCS_PHOTOS_BUCKET:-${GOOGLE_CLOUD_PROJECT}-photos}"
    else
        print_error "Backend failed to start"
    fi

    if check_running "frontend"; then
        print_success "Frontend running at http://localhost:3000"
        print_info "  Hot-reload: Enabled (Next.js Fast Refresh)"
    else
        print_error "Frontend failed to start"
    fi

    if check_running "db"; then
        print_success "PostgreSQL running at localhost:5432"
    else
        print_error "Database failed to start"
    fi

    if check_running "redis"; then
        print_success "Redis running at localhost:6379"
    else
        print_error "Redis failed to start"
    fi

    echo ""
    print_header "Hot-Reload with GCS is Active!"
    echo "Using Google Cloud Storage instead of MinIO"
    echo "Edit your code and watch it reload automatically:"
    echo "  • Backend (Python): ~1 second restart"
    echo "  • Frontend (React): Instant HMR"
    echo ""
    echo "View logs with: ./dev.sh logs"
}

# Function to show logs
logs() {
    SERVICE=${1:-""}

    if [ -z "$SERVICE" ]; then
        print_header "Following All Logs (Ctrl+C to exit)"
        docker-compose logs -f
    else
        print_header "Following $SERVICE Logs (Ctrl+C to exit)"
        docker-compose logs -f "$SERVICE"
    fi
}

# Function to stop services
stop() {
    print_header "Stopping Development Environment"
    docker-compose down
    print_success "All services stopped"
}

# Function to restart a specific service
restart() {
    SERVICE=${1:-""}

    if [ -z "$SERVICE" ]; then
        print_error "Please specify a service: backend, frontend, db, or redis"
        exit 1
    fi

    print_header "Restarting $SERVICE"
    docker-compose restart "$SERVICE"
    print_success "$SERVICE restarted"
}

# Function to rebuild services
rebuild() {
    SERVICE=${1:-""}

    if [ -z "$SERVICE" ]; then
        print_header "Rebuilding All Services"
        docker-compose up -d --build
        print_success "All services rebuilt"
    else
        print_header "Rebuilding $SERVICE"
        docker-compose up -d --build "$SERVICE"
        print_success "$SERVICE rebuilt"
    fi
}

# Function to show status
status() {
    print_header "Services Status"
    docker-compose ps
}

# Function to run backend shell
shell() {
    SERVICE=${1:-"backend"}

    print_header "Opening Shell in $SERVICE"
    docker-compose exec "$SERVICE" /bin/sh
}

# Function to test hot-reload
test_reload() {
    print_header "Testing Hot-Reload"

    print_info "Testing Backend Hot-Reload..."
    TEMP_FILE="backend/app/_test_reload.py"
    echo "# Test file for hot-reload" > "$TEMP_FILE"
    echo "TEST = 'Hot reload works!'" >> "$TEMP_FILE"

    print_info "Created test file: $TEMP_FILE"
    print_info "Check backend logs for reload message:"
    docker-compose logs --tail=10 backend | grep -i "reload" || true

    rm "$TEMP_FILE"
    print_success "Test file removed"

    print_info "Testing Frontend Hot-Reload..."
    print_info "Open http://localhost:3000 and edit any .tsx file"
    print_info "Changes should appear instantly in the browser!"
}

# Function to show help
help() {
    cat << EOF
Development Helper Script for AppArt Agent

Usage: ./dev.sh [command] [options]

Commands:
    start               Start all services with hot-reload (uses MinIO)
    start-gcs           Start services using GCS instead of MinIO
    stop                Stop all services
    restart [service]   Restart a specific service (backend, frontend, db, redis)
    rebuild [service]   Rebuild and restart service(s)
    logs [service]      Follow logs (all services or specific one)
    status              Show services status
    shell [service]     Open shell in container (default: backend)
    test                Test hot-reload functionality
    help                Show this help message

Examples:
    ./dev.sh start                  # Start with MinIO (default)
    ./dev.sh start-gcs              # Start with Google Cloud Storage
    ./dev.sh logs backend           # Follow backend logs
    ./dev.sh restart frontend       # Restart just frontend
    ./dev.sh rebuild backend        # Rebuild backend image
    ./dev.sh shell backend          # Open backend shell

GCS Mode Requirements:
    export GOOGLE_CLOUD_PROJECT=your-project-id
    export GCS_DOCUMENTS_BUCKET=your-documents-bucket  # Optional
    export GCS_PHOTOS_BUCKET=your-photos-bucket        # Optional
    gcloud auth application-default login              # For credentials

Hot-Reload Info:
    • Backend: Uvicorn --reload monitors .py files
    • Frontend: Next.js Fast Refresh for instant updates
    • Edit any file and it reloads automatically!

EOF
}

# Main script
case "${1:-help}" in
    start)
        start
        ;;
    start-gcs)
        start_gcs
        ;;
    stop)
        stop
        ;;
    restart)
        restart "$2"
        ;;
    rebuild)
        rebuild "$2"
        ;;
    logs)
        logs "$2"
        ;;
    status)
        status
        ;;
    shell)
        shell "$2"
        ;;
    test)
        test_reload
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
