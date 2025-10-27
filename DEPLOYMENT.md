# Audio Fingerprinting System - Deployment Guide

This guide covers deploying the Audio Fingerprinting System using Docker containers in both development and production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Memory**: Minimum 2GB RAM, 4GB+ recommended for production
- **Storage**: Minimum 10GB free space, 50GB+ recommended for production
- **CPU**: 2+ cores recommended

### Software Requirements

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **Git**: For cloning the repository
- **OpenSSL**: For generating certificates and keys

### Installation

#### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
```

#### macOS
```bash
# Install Docker Desktop from https://docker.com/products/docker-desktop
# Or using Homebrew
brew install --cask docker
```

#### Windows
Install Docker Desktop from https://docker.com/products/docker-desktop

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd audio-fingerprinting-system
   ```

2. **Run the deployment script**
   ```bash
   # For development
   ./scripts/deploy.sh deploy development
   
   # For production
   ./scripts/deploy.sh deploy production
   ```

3. **Access the application**
   - API Documentation: http://localhost/docs
   - Health Check: http://localhost/health
   - API Endpoint: http://localhost/api/v1/identify

## Development Deployment

### Setup

1. **Prepare environment**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit configuration (optional for development)
   nano .env
   ```

2. **Deploy development environment**
   ```bash
   ./scripts/deploy.sh deploy development
   ```

3. **Verify deployment**
   ```bash
   # Check service status
   ./scripts/deploy.sh status
   
   # View logs
   ./scripts/deploy.sh logs
   ```

### Development Features

- **Hot Reload**: Code changes are automatically reflected
- **Debug Logging**: Detailed logs for troubleshooting
- **Relaxed Security**: CORS and host restrictions disabled
- **Sample Data**: Automatically populated with test songs

### Development URLs

- API: http://localhost:8001
- Database: localhost:5433
- Redis: localhost:6380

## Production Deployment

### Initial Setup

1. **Run production setup script**
   ```bash
   sudo ./scripts/setup-production.sh
   ```

2. **Configure environment**
   ```bash
   # Edit production environment file
   nano .env.production
   
   # Update critical settings:
   # - DB_PASSWORD: Strong database password
   # - ADMIN_API_KEY: Secure API key
   # - ALLOWED_HOSTS: Your domain names
   # - CORS_ORIGINS: Your frontend domains
   ```

3. **Setup SSL certificates**
   ```bash
   # For production, replace self-signed certificates
   # Copy your SSL certificate and key to nginx/ssl/
   cp your-cert.pem nginx/ssl/cert.pem
   cp your-key.pem nginx/ssl/key.pem
   ```

### Deploy Production

1. **Deploy the system**
   ```bash
   ./scripts/deploy.sh deploy production
   ```

2. **Verify deployment**
   ```bash
   # Check all services are healthy
   docker ps
   
   # Test API health
   curl http://localhost/health
   ```

3. **Setup monitoring** (optional)
   ```bash
   # Deploy monitoring stack
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

### Production URLs

- API: http://localhost (or your domain)
- Database: Internal only (port 5432)
- Redis: Internal only (port 6379)

## Configuration

### Environment Variables

Key configuration options:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DB_PASSWORD` | Database password | - | Yes |
| `ADMIN_API_KEY` | Admin API key | - | Yes |
| `ALLOWED_HOSTS` | Allowed host names | `*` | Production |
| `CORS_ORIGINS` | CORS allowed origins | `*` | Production |
| `MAX_REQUEST_SIZE` | Max upload size | `50MB` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Database Configuration

The system uses PostgreSQL with the following optimizations:

- **Connection Pooling**: 10-20 connections
- **Indexes**: Optimized for fingerprint matching
- **Extensions**: pg_stat_statements for monitoring

### Performance Tuning

#### For High Load

```bash
# Increase database connections
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100

# Increase request timeout
REQUEST_TIMEOUT_SECONDS=60

# Enable Redis caching
REDIS_URL=redis://redis:6379/0
```

#### For Large Databases

```bash
# Increase fingerprint match limits
MAX_FINGERPRINT_MATCHES=5000

# Optimize database queries
DATABASE_QUERY_TIMEOUT_SECONDS=10
```

## Monitoring

### Health Checks

- **API Health**: `GET /api/v1/admin/health`
- **Database**: Automatic connection testing
- **Audio Engine**: Component status verification

### Metrics

Access metrics at `/api/v1/admin/metrics`:

- Request counts and response times
- Database query performance
- Audio processing statistics
- System resource usage

### Logging

Logs are stored in the `logs/` directory:

- `api.log`: Application logs
- `nginx/access.log`: HTTP access logs
- `nginx/error.log`: HTTP error logs

### Alerting

Configure alerts for:

- High response times (>10 seconds)
- High error rates (>5%)
- Database connection failures
- Disk space usage (>80%)

## Backup and Recovery

### Automated Backups

Backups run daily at 2 AM and include:

- Database dump
- Configuration files
- Recent logs

```bash
# Manual backup
./scripts/backup.sh

# Restore from backup
./scripts/restore.sh backup_20231027_020000.tar.gz
```

### Database Backup

```bash
# Create database backup
docker exec audio_fingerprinting_db pg_dump -U audio_user -Fc audio_fingerprinting > backup.dump

# Restore database backup
docker exec -i audio_fingerprinting_db pg_restore -U audio_user -d audio_fingerprinting < backup.dump
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose logs

# Restart services
./scripts/deploy.sh restart
```

#### Database Connection Errors

```bash
# Check database status
docker exec audio_fingerprinting_db pg_isready -U audio_user

# Reset database
docker-compose down -v
./scripts/deploy.sh deploy
```

#### High Memory Usage

```bash
# Check container resources
docker stats

# Restart API service
docker-compose restart api
```

#### Audio Processing Errors

```bash
# Check audio engine
docker exec audio_fingerprinting_api python -c "import audio_fingerprint_engine; print('OK')"

# Rebuild audio engine
docker-compose build --no-cache api
```

### Performance Issues

#### Slow Response Times

1. Check database indexes:
   ```sql
   SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
   ```

2. Monitor query performance:
   ```sql
   SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
   ```

3. Increase resources:
   ```bash
   # Edit docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '2.0'
   ```

#### High CPU Usage

1. Check concurrent requests
2. Optimize audio processing
3. Scale horizontally:
   ```bash
   docker-compose up --scale api=3
   ```

### Getting Help

1. **Check logs**: `./scripts/deploy.sh logs`
2. **Verify configuration**: Review `.env` file
3. **Test components**: Use health check endpoints
4. **Monitor resources**: `docker stats`

### Support

For additional support:

- Check the project documentation
- Review GitHub issues
- Contact the development team

## Security Considerations

### Production Security

1. **Change default passwords**
2. **Use strong API keys**
3. **Configure proper CORS origins**
4. **Set up SSL/TLS certificates**
5. **Regular security updates**
6. **Monitor access logs**
7. **Implement rate limiting**

### Network Security

```bash
# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # Block external database access
```

### Data Protection

- Regular backups
- Encrypted connections
- Access logging
- Data retention policies

## Scaling

### Horizontal Scaling

```bash
# Scale API instances
docker-compose up --scale api=3

# Use load balancer
# Configure nginx upstream with multiple API instances
```

### Vertical Scaling

```bash
# Increase container resources
# Edit docker-compose.yml deploy.resources section
```

### Database Scaling

- Read replicas for query scaling
- Connection pooling optimization
- Database partitioning for large datasets