#!/bin/bash

# BI Self-Service Chatbot Deployment Script
# This script deploys the chatbot to your existing BI infrastructure

set -e

echo "🚀 Deploying BI Self-Service Chatbot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the bi_selfservice directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from example..."
    if [ -f "config.env.example" ]; then
        cp config.env.example .env
        print_status "Created .env file from example. Please edit it with your configuration."
    else
        print_error "config.env.example not found. Please create a .env file manually."
        exit 1
    fi
fi

# Check required environment variables
print_status "Checking environment configuration..."

# Source the .env file
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required variables
required_vars=("DATABASE_URL" "OPENAI_API_KEY" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables: ${missing_vars[*]}"
    print_status "Please update your .env file with the required values."
    exit 1
fi

print_status "Environment configuration looks good!"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install it and try again."
    exit 1
fi

# Build and deploy
print_status "Building Docker images..."
docker-compose build

print_status "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Check service health
print_status "Checking service health..."

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ API service is healthy"
else
    print_warning "⚠️  API service health check failed"
fi

# Check web interface
if curl -f http://localhost:8080 > /dev/null 2>&1; then
    print_status "✅ Web interface is accessible"
else
    print_warning "⚠️  Web interface health check failed"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "✅ Redis is running"
else
    print_warning "⚠️  Redis health check failed"
fi

print_status "🎉 Deployment completed!"
echo ""
echo "📋 Service URLs:"
echo "   Web Interface: http://localhost:8080"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "🔧 Next steps:"
echo "   1. Access the web interface at http://localhost:8080"
echo "   2. Try asking questions like:"
echo "      - 'Show me user leads for last month'"
echo "      - 'What are the top performing projects by leads?'"
echo "      - 'Compare leads between different marketing channels'"
echo ""
echo "📊 Monitoring:"
echo "   - View logs: docker-compose logs -f"
echo "   - Check status: docker-compose ps"
echo "   - Stop services: docker-compose down"
echo ""
echo "🔒 Security notes:"
echo "   - Change default passwords in production"
echo "   - Configure proper authentication"
echo "   - Set up SSL/TLS certificates"
echo "   - Restrict database access to read-only" 