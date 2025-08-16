#!/bin/bash

# RunPod optimized startup script for AI-Dev
# Designed for uncensored operation with HTTPS support

set -e

echo "=== AI-Dev RunPod Server Starting ==="

# RunPod specific configurations
export HOST=${HOST:-"127.0.0.1"}
export PORT=${PORT:-"8080"}
export WORKERS=${WORKERS:-"4"}
export MAX_WORKERS=${MAX_WORKERS:-"8"}

# Uncensored operation settings
export DISABLE_CONTENT_FILTER=${DISABLE_CONTENT_FILTER:-"true"}
export ALLOW_UNSAFE_CODE=${ALLOW_UNSAFE_CODE:-"true"}
export BYPASS_SAFETY_CHECKS=${BYPASS_SAFETY_CHECKS:-"true"}
export UNCENSORED_MODE=${UNCENSORED_MODE:-"true"}

# Performance optimizations for RunPod
export TORCH_CUDA_ARCH_LIST="6.0;6.1;7.0;7.5;8.0;8.6"
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-"0"}
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-"4"}

# LLM Backend configuration
export LLM_BACKEND=${LLM_BACKEND:-"openai"}
export VECTOR_BACKEND=${VECTOR_BACKEND:-"qdrant"}

# Model settings for uncensored operation
export MODEL_TEMPERATURE=${MODEL_TEMPERATURE:-"0.9"}
export MODEL_TOP_P=${MODEL_TOP_P:-"0.95"}
export MODEL_MAX_TOKENS=${MODEL_MAX_TOKENS:-"4096"}
export ENABLE_SYSTEM_PROMPTS=${ENABLE_SYSTEM_PROMPTS:-"true"}

# Security bypass settings (for uncensored operation)
export DISABLE_MODERATION=${DISABLE_MODERATION:-"true"}
export SKIP_CONTENT_VALIDATION=${SKIP_CONTENT_VALIDATION:-"true"}
export ALLOW_ALL_REQUESTS=${ALLOW_ALL_REQUESTS:-"true"}

# RunPod environment detection
if [ -n "$RUNPOD_POD_ID" ]; then
    echo "Running on RunPod Pod: $RUNPOD_POD_ID"
    export RUNPOD_MODE="true"
    
    # Use RunPod's public URL if available
    if [ -n "$RUNPOD_PUBLIC_IP" ]; then
        export PUBLIC_URL="https://${RUNPOD_PUBLIC_IP}:8443"
    fi
fi

# Verify API keys based on backend
case "$LLM_BACKEND" in
    "openai")
        if [ -z "$OPENAI_API_KEY" ]; then
            echo "Warning: OPENAI_API_KEY not set. Some features may not work."
        fi
        ;;
    "anthropic")
        if [ -z "$ANTHROPIC_API_KEY" ]; then
            echo "Warning: ANTHROPIC_API_KEY not set. Some features may not work."
        fi
        ;;
    "local"|"ollama")
        echo "Using local LLM backend - no API key required"
        ;;
esac

# Vector database configuration
case "$VECTOR_BACKEND" in
    "qdrant")
        export QDRANT_URL=${QDRANT_URL:-"http://localhost:6333"}
        ;;
    "pinecone")
        if [ -z "$PINECONE_API_KEY" ]; then
            echo "Warning: PINECONE_API_KEY not set for Pinecone backend"
        fi
        ;;
    "local")
        echo "Using local vector storage"
        ;;
esac

# Create necessary directories
mkdir -p /app/.runs /app/data /app/logs

# Set up Python environment
export PYTHONPATH="/app:${PYTHONPATH}"
export PYTHONUNBUFFERED=1

# Configure nginx for HTTPS
echo "Setting up nginx configuration..."
ln -sf /app/cloud/runpod/nginx/sites-available/ai-dev /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

echo "Configuration Summary:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  LLM Backend: $LLM_BACKEND"
echo "  Vector Backend: $VECTOR_BACKEND"
echo "  Uncensored Mode: $UNCENSORED_MODE"
echo "  Public URL: ${PUBLIC_URL:-"Not set"}"

# Start the FastAPI application
echo "=== Starting AI-Dev API Server ==="

exec uvicorn api.server:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --access-log \
    --log-level info \
    --loop uvloop \
    --http httptools
