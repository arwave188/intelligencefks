FROM python:3.11-slim

# Install system dependencies including SSL/TLS support
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    ca-certificates \
    openssl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 app && \
    mkdir -p /app && \
    chown app:app /app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations for RunPod
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/.runs /app/data /app/logs /var/log/supervisor /etc/ssl/certs/ai-dev && \
    chown -R app:app /app

# Copy RunPod configuration files
COPY cloud/runpod/supervisor/ /etc/supervisor/
COPY cloud/runpod/nginx/ /etc/nginx/

# Generate self-signed SSL certificate for HTTPS
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/certs/ai-dev/server.key \
    -out /etc/ssl/certs/ai-dev/server.crt \
    -subj "/C=US/ST=State/L=City/O=AI-Dev/CN=localhost"

# Set proper permissions for SSL certificates
RUN chmod 600 /etc/ssl/certs/ai-dev/server.key && \
    chmod 644 /etc/ssl/certs/ai-dev/server.crt

# Set Python path and environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Expose ports for HTTP and HTTPS
EXPOSE 8000 8443

# Use supervisor to manage multiple processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
