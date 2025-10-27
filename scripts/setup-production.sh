#!/bin/bash
# Production setup script for Audio Fingerprinting System

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Function to setup SSL certificates
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    local ssl_dir="$PROJECT_ROOT/nginx/ssl"
    mkdir -p "$ssl_dir"
    
    # Generate self-signed certificate for development/testing
    if [ ! -f "$ssl_dir/cert.pem" ] || [ ! -f "$ssl_dir/key.pem" ]; then
        log_info "Generating self-signed SSL certificate..."
        
        openssl req -x509 -newkey rsa:4096 -keyout "$ssl_dir/key.pem" -out "$ssl_dir/cert.pem" \
            -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        chmod 600 "$ssl_dir/key.pem"
        chmod 644 "$ssl_dir/cert.pem"
        
        log_success "Self-signed SSL certificate generated"
        log_warning "For production, replace with a proper SSL certificate from a CA"
    else
        log_info "SSL certificates already exist"
    fi
}

# Function to setup production environment file
setup_production_env() {
    log_info "Setting up production environment..."
    
    local env_file="$PROJECT_ROOT/.env.production"
    
    if [ ! -f "$env_file" ]; then
        log_info "Creating production environment file..."
        
        # Generate secure passwords and keys
        local db_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        local admin_api_key=$(openssl rand -hex 32)
        local secret_key=$(openssl rand -hex 32)
        
        cat > "$env_file" << EOF
# Production Environment Configuration
# Generated on $(date)

# Database Configuration
DB_PASSWORD=$db_password
DATABASE_URL=postgresql://audio_user:$db_password@database:5432/audio_fingerprinting
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30

# API Configuration
API_TITLE=Audio Fingerprinting API
API_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=$secret_key

# Security Configuration
ADMIN_API_KEY=$admin_api_key
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Performance Configuration
MAX_REQUEST_SIZE=52428800  # 50MB
REQUEST_TIMEOUT_SECONDS=30
AUDIO_PROCESSING_TIMEOUT_SECONDS=10
DATABASE_QUERY_TIMEOUT_SECONDS=5
MAX_AUDIO_DURATION_MS=30000

# Audio Processing Configuration
AUDIO_SAMPLE_RATE=44100
FINGERPRINT_CONFIDENCE_THRESHOLD=0.3
MAX_FINGERPRINT_MATCHES=1000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis Configuration (for caching)
REDIS_URL=redis://redis:6379/0

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090

# Backup Configuration
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
EOF
        
        chmod 600 "$env_file"
        
        log_success "Production environment file created: $env_file"
        log_warning "Please review and update the configuration, especially:"
        log_warning "  - ALLOWED_HOSTS: Add your actual domain names"
        log_warning "  - CORS_ORIGINS: Add your frontend domain names"
        log_warning "  - Database and API credentials"
    else
        log_info "Production environment file already exists"
    fi
}

# Function to setup systemd service (for non-Docker deployments)
setup_systemd_service() {
    log_info "Setting up systemd service..."
    
    local service_file="/etc/systemd/system/audio-fingerprinting.service"
    
    if [ ! -f "$service_file" ] && [ "$EUID" -eq 0 ]; then
        cat > "$service_file" << EOF
[Unit]
Description=Audio Fingerprinting API Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_ROOT
ExecStart=/usr/bin/docker-compose -f docker-compose.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
        
        systemctl daemon-reload
        systemctl enable audio-fingerprinting.service
        
        log_success "Systemd service created and enabled"
        log_info "Use 'systemctl start audio-fingerprinting' to start the service"
    elif [ "$EUID" -ne 0 ]; then
        log_warning "Skipping systemd service setup (requires root privileges)"
    else
        log_info "Systemd service already exists"
    fi
}

# Function to setup log rotation
setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    local logrotate_file="/etc/logrotate.d/audio-fingerprinting"
    
    if [ ! -f "$logrotate_file" ] && [ "$EUID" -eq 0 ]; then
        cat > "$logrotate_file" << EOF
$PROJECT_ROOT/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker exec audio_fingerprinting_api kill -USR1 1 2>/dev/null || true
    endscript
}

$PROJECT_ROOT/logs/nginx/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker exec audio_fingerprinting_nginx nginx -s reload 2>/dev/null || true
    endscript
}
EOF
        
        log_success "Log rotation configured"
    elif [ "$EUID" -ne 0 ]; then
        log_warning "Skipping log rotation setup (requires root privileges)"
    else
        log_info "Log rotation already configured"
    fi
}

# Function to setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring configuration..."
    
    local monitoring_dir="$PROJECT_ROOT/monitoring"
    mkdir -p "$monitoring_dir"
    
    # Create Prometheus configuration
    if [ ! -f "$monitoring_dir/prometheus.yml" ]; then
        cat > "$monitoring_dir/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'audio-fingerprinting-api'
    static_configs:
      - targets: ['api:9090']
    metrics_path: '/api/v1/admin/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['database:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
EOF
        
        log_success "Prometheus configuration created"
    fi
    
    # Create alert rules
    if [ ! -f "$monitoring_dir/alert_rules.yml" ]; then
        cat > "$monitoring_dir/alert_rules.yml" << EOF
groups:
  - name: audio_fingerprinting_alerts
    rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ \$value }}s"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ \$value }} errors per second"

      - alert: DatabaseConnectionFailure
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "Cannot connect to PostgreSQL database"
EOF
        
        log_success "Alert rules created"
    fi
}

# Function to setup backup script
setup_backup_script() {
    log_info "Setting up backup script..."
    
    local backup_script="$PROJECT_ROOT/scripts/backup.sh"
    
    if [ ! -f "$backup_script" ]; then
        cat > "$backup_script" << 'EOF'
#!/bin/bash
# Automated backup script for Audio Fingerprinting System

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$DATE"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Create backup directory
mkdir -p "$BACKUP_PATH"

echo "Starting backup: $BACKUP_NAME"

# Backup database
echo "Backing up database..."
docker exec audio_fingerprinting_db pg_dump -U audio_user -Fc audio_fingerprinting > "$BACKUP_PATH/database.dump"

# Backup configuration files
echo "Backing up configuration..."
cp "$PROJECT_ROOT/.env" "$BACKUP_PATH/" 2>/dev/null || true
cp "$PROJECT_ROOT/.env.production" "$BACKUP_PATH/" 2>/dev/null || true

# Backup logs (last 7 days)
echo "Backing up recent logs..."
find "$PROJECT_ROOT/logs" -name "*.log" -mtime -7 -exec cp {} "$BACKUP_PATH/" \; 2>/dev/null || true

# Compress backup
echo "Compressing backup..."
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete 2>/dev/null || true

echo "Backup completed: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
EOF
        
        chmod +x "$backup_script"
        log_success "Backup script created"
    fi
    
    # Setup cron job for automated backups
    if [ "$EUID" -eq 0 ]; then
        local cron_job="0 2 * * * $backup_script >> $PROJECT_ROOT/logs/backup.log 2>&1"
        
        if ! crontab -l 2>/dev/null | grep -q "$backup_script"; then
            (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
            log_success "Automated backup scheduled (daily at 2 AM)"
        fi
    else
        log_warning "Skipping cron job setup (requires root privileges)"
        log_info "To setup automated backups, run as root or add to crontab manually:"
        log_info "  0 2 * * * $backup_script >> $PROJECT_ROOT/logs/backup.log 2>&1"
    fi
}

# Function to perform security hardening
security_hardening() {
    log_info "Applying security hardening..."
    
    # Set proper file permissions
    find "$PROJECT_ROOT" -name "*.sh" -exec chmod +x {} \;
    find "$PROJECT_ROOT" -name ".env*" -exec chmod 600 {} \; 2>/dev/null || true
    
    # Create security configuration
    local security_conf="$PROJECT_ROOT/nginx/conf.d/security.conf"
    if [ ! -f "$security_conf" ]; then
        cat > "$security_conf" << EOF
# Security headers
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

# Hide server information
server_tokens off;
more_clear_headers Server;

# Rate limiting for security
limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;
limit_req_zone \$binary_remote_addr zone=api_strict:10m rate=5r/s;
EOF
        
        log_success "Security configuration created"
    fi
    
    log_success "Security hardening completed"
}

# Function to run system checks
run_system_checks() {
    log_info "Running system checks..."
    
    # Check available disk space
    local available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    local required_space=1048576  # 1GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        log_warning "Low disk space: $(($available_space / 1024))MB available, 1GB recommended"
    fi
    
    # Check memory
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    local required_memory=512
    
    if [ "$available_memory" -lt "$required_memory" ]; then
        log_warning "Low memory: ${available_memory}MB available, ${required_memory}MB recommended"
    fi
    
    # Check Docker resources
    if command -v docker &> /dev/null; then
        local docker_info=$(docker system df 2>/dev/null || echo "")
        if [ -n "$docker_info" ]; then
            log_info "Docker system resources:"
            echo "$docker_info"
        fi
    fi
    
    log_success "System checks completed"
}

# Main setup function
main() {
    log_info "Starting production setup for Audio Fingerprinting System..."
    
    # Check if running as root for some operations
    if [ "$EUID" -eq 0 ]; then
        log_info "Running as root - full setup available"
    else
        log_warning "Not running as root - some features will be skipped"
    fi
    
    # Run setup steps
    run_system_checks
    setup_production_env
    setup_ssl
    setup_monitoring
    setup_backup_script
    setup_log_rotation
    setup_systemd_service
    security_hardening
    
    log_success "Production setup completed!"
    echo
    log_info "Next steps:"
    echo "  1. Review and update .env.production with your specific configuration"
    echo "  2. Replace self-signed SSL certificates with proper CA certificates"
    echo "  3. Update ALLOWED_HOSTS and CORS_ORIGINS for your domain"
    echo "  4. Run './scripts/deploy.sh deploy production' to start the system"
    echo "  5. Configure your firewall to allow ports 80 and 443"
    echo "  6. Set up external monitoring and alerting"
}

# Run main function
main "$@"