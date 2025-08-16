#!/bin/bash

# AI-Dev RunPod Deployment Script
# This script helps deploy AI-Dev to RunPod with HTTPS and uncensored operation

set -e

echo "🚀 AI-Dev RunPod Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running on RunPod
if [ -n "$RUNPOD_POD_ID" ]; then
    print_status "Detected RunPod environment (Pod ID: $RUNPOD_POD_ID)"
    export RUNPOD_MODE=true
else
    print_warning "Not running on RunPod - this script is optimized for RunPod"
fi

# Step 1: Environment Setup
print_step "1. Setting up environment..."

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.runpod" ]; then
        cp .env.runpod .env
        print_status "Created .env from template"
    else
        print_error ".env.runpod template not found!"
        exit 1
    fi
fi

# Source environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
    print_status "Loaded environment variables"
fi

# Step 2: Validate API Keys
print_step "2. Validating API keys..."

api_key_missing=false

if [ "$LLM_BACKEND" = "openai" ] && [ -z "$OPENAI_API_KEY" ]; then
    print_error "OPENAI_API_KEY is required for OpenAI backend"
    api_key_missing=true
fi

if [ "$LLM_BACKEND" = "anthropic" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    print_error "ANTHROPIC_API_KEY is required for Anthropic backend"
    api_key_missing=true
fi

if [ "$VECTOR_BACKEND" = "pinecone" ] && [ -z "$PINECONE_API_KEY" ]; then
    print_error "PINECONE_API_KEY is required for Pinecone backend"
    api_key_missing=true
fi

if [ "$api_key_missing" = true ]; then
    print_error "Please configure your API keys in .env file"
    exit 1
fi

print_status "API keys validation passed"

# Step 3: Create necessary directories
print_step "3. Creating directories..."

mkdir -p .runs data logs
mkdir -p /etc/ssl/certs/ai-dev 2>/dev/null || true

print_status "Directories created"

# Step 4: Generate SSL certificates if needed
print_step "4. Setting up SSL certificates..."

if [ ! -f "/etc/ssl/certs/ai-dev/server.crt" ] || [ ! -f "/etc/ssl/certs/ai-dev/server.key" ]; then
    print_status "Generating self-signed SSL certificate..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/certs/ai-dev/server.key \
        -out /etc/ssl/certs/ai-dev/server.crt \
        -subj "/C=US/ST=RunPod/L=Cloud/O=AI-Dev/CN=localhost" 2>/dev/null || {
        
        # Fallback: create in local directory if /etc/ssl is not writable
        mkdir -p ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/server.key \
            -out ssl/server.crt \
            -subj "/C=US/ST=RunPod/L=Cloud/O=AI-Dev/CN=localhost"
        
        export SSL_CERT_PATH="$(pwd)/ssl/server.crt"
        export SSL_KEY_PATH="$(pwd)/ssl/server.key"
        
        print_status "SSL certificates created in local directory"
    }
else
    print_status "SSL certificates already exist"
fi

# Step 5: Install dependencies
print_step "5. Installing dependencies..."

if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
    print_status "Dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Step 6: Configure nginx (if available)
print_step "6. Configuring nginx..."

if command -v nginx >/dev/null 2>&1; then
    # Copy nginx configuration
    if [ -f "cloud/runpod/nginx/sites-available/ai-dev" ]; then
        sudo cp cloud/runpod/nginx/sites-available/ai-dev /etc/nginx/sites-available/ 2>/dev/null || {
            print_warning "Cannot copy nginx config - insufficient permissions"
        }
        
        sudo ln -sf /etc/nginx/sites-available/ai-dev /etc/nginx/sites-enabled/ 2>/dev/null || {
            print_warning "Cannot enable nginx site - insufficient permissions"
        }
        
        sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
        
        # Test nginx configuration
        sudo nginx -t 2>/dev/null && print_status "Nginx configuration valid" || {
            print_warning "Nginx configuration test failed"
        }
    fi
else
    print_warning "Nginx not available - using direct FastAPI serving"
fi

# Step 7: Display configuration summary
print_step "7. Configuration Summary"
echo "=========================="
echo "LLM Backend: $LLM_BACKEND"
echo "Vector Backend: $VECTOR_BACKEND"
echo "Uncensored Mode: ${UNCENSORED_MODE:-true}"
echo "SSL Enabled: ${SSL_ENABLED:-true}"
echo "Host: ${HOST:-127.0.0.1}"
echo "Port: ${PORT:-8080}"
echo "Workers: ${WORKERS:-4}"

if [ -n "$RUNPOD_PUBLIC_IP" ]; then
    echo "Public HTTPS URL: https://$RUNPOD_PUBLIC_IP:8443"
fi

echo "=========================="

# Step 8: Start the application
print_step "8. Starting AI-Dev..."

if [ "$1" = "--start" ]; then
    print_status "Starting AI-Dev server..."
    exec bash cloud/runpod/start_runpod.sh
else
    print_status "Setup complete! Run with --start to launch the server:"
    echo "bash cloud/deploy_runpod.sh --start"
fi
