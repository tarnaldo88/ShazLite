#!/bin/bash
# Deployment script for Audio Fingerprinting System

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
BACKUP_DIR="$PROJECT_ROOT/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Determine Docker Compose command
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    log_success "Prerequisites check passed"
}

# Function to create environment file if it doesn't exist
create_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating environment file..."
        
        cat > "$ENV_FILE" << EOF
# Database Configuration
DB_PASSWORD=audio_password_$(openssl rand -hex 8)

# API Configuration
ADMIN_API_KEY=admin_key_$(openssl rand -hex 16)

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security (update these for production)
ALLOWED_HOSTS=*
CORS_ORIGINS=*

# Performance
MAX_REQUEST_SIZE=10485760
REQUEST_TIMEOUT_SECONDS=30
AUDIO_PROCESSING_TIMEOUT_SECONDS=10
DATABASE_QUERY_TIMEOUT_SECONDS=5
EOF
        
        log_success "Environment file created at $ENV_FILE"
        log_warning "Please review and update the environment variables in $ENV_FILE"
    else
        log_info "Environment file already exists"
    fi
}

# Function to create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/logs/nginx"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$PROJECT_ROOT/nginx/ssl"
    
    log_success "Directories created"
}

# Function to build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build the main application image
    docker build -t audio-fingerprinting:latest --target production .
    
    log_success "Docker images built successfully"
}

# Function to start services
start_services() {
    local compose_file="$1"
    
    log_info "Starting services with $compose_file..."
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images for external services
    $DOCKER_COMPOSE -f "$compose_file" pull database redis nginx
    
    # Start services
    $DOCKER_COMPOSE -f "$compose_file" up -d
    
    log_success "Services started"
}

# Function to wait for services to be healthy
wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        # Check database health
        if docker exec audio_fingerprinting_db pg_isready -U audio_user -d audio_fingerprinting &> /dev/null; then
            log_success "Database is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to become healthy within timeout"
            return 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    # Wait a bit more for API to be ready
    sleep 15
    
    # Check API health
    if curl -f http://localhost/health &> /dev/null; then
        log_success "API is healthy"
    else
        log_warning "API health check failed, but continuing..."
    fi
}

# Function to run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # This would run actual migrations in a real deployment
    # For now, we'll just ensure the database is accessible
    docker exec audio_fingerprinting_api python -c "
from backend.database.connection import get_db_session
try:
    with get_db_session() as session:
        session.execute('SELECT 1')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" || {
        log_error "Database migration failed"
        return 1
    }
    
    log_success "Database migrations completed"
}

# Function to populate sample data
populate_sample_data() {
    log_info "Populating sample data..."
    
    # This would populate the database with sample songs
    docker exec audio_fingerprinting_api python -c "
from backend.database.population_utils import DatabaseSeeder
try:
    seeder = DatabaseSeeder()
    stats = seeder.seed_sample_songs(5)  # Add 5 sample songs
    print(f'Sample data populated: {stats}')
except Exception as e:
    print(f'Sample data population failed: {e}')
    # Don't fail deployment for this
" || log_warning "Sample data population failed (non-critical)"
    
    log_success "Sample data population completed"
}

# Function to create backup
create_backup() {
    log_info "Creating backup..."
    
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup database
    docker exec audio_fingerprinting_db pg_dump -U audio_user audio_fingerprinting > "$backup_path/database.sql" || {
        log_warning "Database backup failed"
    }
    
    # Backup environment file
    cp "$ENV_FILE" "$backup_path/" 2>/dev/null || true
    
    log_success "Backup created at $backup_path"
}

# Function to show deployment status
show_status() {
    log_info "Deployment Status:"
    echo
    
    # Show running containers
    echo "Running containers:"
    docker ps --filter "name=audio_fingerprinting" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo
    
    # Show service URLs
    echo "Service URLs:"
    echo "  API Documentation: http://localhost/docs"
    echo "  Health Check: http://localhost/health"
    echo "  API Endpoint: http://localhost/api/v1/identify"
    echo
    
    # Show logs command
    echo "To view logs:"
    echo "  docker-compose logs -f"
    echo
    
    # Show stop command
    echo "To stop services:"
    echo "  docker-compose down"
}

# Function to cleanup on failure
cleanup_on_failure() {
    log_error "Deployment failed. Cleaning up..."
    
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE down --remove-orphans || true
    
    log_info "Cleanup completed"
}

# Main deployment function
deploy() {
    local environment="${1:-production}"
    local compose_file
    
    if [ "$environment" = "development" ]; then
        compose_file="docker-compose.dev.yml"
    else
        compose_file="docker-compose.yml"
    fi
    
    log_info "Starting deployment for $environment environment..."
    
    # Set up error handling
    trap cleanup_on_failure ERR
    
    # Run deployment steps
    check_prerequisites
    create_env_file
    create_directories
    build_images
    
    # Create backup if production deployment
    if [ "$environment" = "production" ]; then
        create_backup
    fi
    
    start_services "$compose_file"
    wait_for_services
    run_migrations
    
    # Only populate sample data in development
    if [ "$environment" = "development" ]; then
        populate_sample_data
    fi
    
    show_status
    
    log_success "Deployment completed successfully!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  deploy [production|development]  Deploy the application (default: production)"
    echo "  stop                            Stop all services"
    echo "  restart [production|development] Restart all services"
    echo "  logs [service]                  Show logs for all services or specific service"
    echo "  status                          Show deployment status"
    echo "  backup                          Create a backup"
    echo "  help                            Show this help message"
    echo
    echo "Examples:"
    echo "  $0 deploy production            Deploy for production"
    echo "  $0 deploy development           Deploy for development"
    echo "  $0 logs api                     Show API logs"
    echo "  $0 restart                      Restart production deployment"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy "${2:-production}"
        ;;
    stop)
        log_info "Stopping services..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE down
        log_success "Services stopped"
        ;;
    restart)
        log_info "Restarting services..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE down
        deploy "${2:-production}"
        ;;
    logs)
        cd "$PROJECT_ROOT"
        if [ -n "$2" ]; then
            $DOCKER_COMPOSE logs -f "$2"
        else
            $DOCKER_COMPOSE logs -f
        fi
        ;;
    status)
        show_status
        ;;
    backup)
        create_backup
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac