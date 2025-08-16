# 🚀 AI-Dev RunPod Deployment Guide

Deploy your AI-Dev agent on RunPod with HTTPS support and **100% uncensored operation**.

## 🔥 Features

- ✅ **100% Uncensored Operation** - No content filtering or safety restrictions
- ✅ **HTTPS/SSL Support** - Secure connections with automatic certificate generation
- ✅ **RunPod Optimized** - Configured for RunPod's GPU infrastructure
- ✅ **High Performance** - Multi-worker setup with GPU acceleration
- ✅ **Easy Deployment** - One-click setup with automated scripts

## 🚀 Quick Start

### 1. Create RunPod Instance

1. Go to [RunPod Console](https://console.runpod.io/)
2. Click "Deploy" → "New Pod"
3. Choose a GPU instance (RTX 4090, A100, etc.)
4. Select "Custom Container" template
5. Use this Docker image: `python:3.11-slim`

### 2. Upload Your Code

Upload your AI-Dev codebase to the RunPod instance:

```bash
# Option 1: Git clone (recommended)
git clone https://github.com/your-username/ai-dev.git
cd ai-dev

# Option 2: Upload via RunPod file manager
# Use the web interface to upload your files
```

### 3. Configure Environment

Copy and edit the environment file:

```bash
cp .env.runpod .env
nano .env
```

**Required Configuration:**

```bash
# API Keys (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Uncensored Operation (ENABLED BY DEFAULT)
UNCENSORED_MODE=true
DISABLE_CONTENT_FILTER=true
ALLOW_UNSAFE_CODE=true
BYPASS_SAFETY_CHECKS=true
```

### 4. Deploy

Run the automated deployment script:

```bash
bash cloud/deploy_runpod.sh --start
```

## 🔧 Manual Deployment

If you prefer manual setup:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Build Docker Image

```bash
docker build -t ai-dev-runpod .
```

### 3. Run with Docker Compose

```bash
docker-compose -f docker-compose.runpod.yml up -d
```

## 🌐 Access Your API

Once deployed, your API will be available at:

- **HTTPS**: `https://your-runpod-ip:8443`
- **HTTP**: `http://your-runpod-ip:8000` (redirects to HTTPS)

### API Endpoints

- **Main API**: `https://your-runpod-ip:8443/`
- **Documentation**: `https://your-runpod-ip:8443/docs`
- **Health Check**: `https://your-runpod-ip:8443/health`

## 🔓 Uncensored Operation

This deployment is configured for **100% uncensored operation**:

### Disabled Safety Features

- ❌ Content filtering disabled
- ❌ Safety checks bypassed  
- ❌ Moderation disabled
- ❌ Content validation skipped
- ❌ Request restrictions removed

### Environment Variables

```bash
UNCENSORED_MODE=true
DISABLE_CONTENT_FILTER=true
ALLOW_UNSAFE_CODE=true
BYPASS_SAFETY_CHECKS=true
DISABLE_MODERATION=true
SKIP_CONTENT_VALIDATION=true
ALLOW_ALL_REQUESTS=true
```

## 🔒 HTTPS Configuration

### Automatic SSL Certificates

The deployment automatically generates self-signed SSL certificates:

- **Certificate**: `/etc/ssl/certs/ai-dev/server.crt`
- **Private Key**: `/etc/ssl/certs/ai-dev/server.key`

### Custom SSL Certificates

To use your own SSL certificates:

1. Replace the generated certificates:
```bash
cp your-certificate.crt /etc/ssl/certs/ai-dev/server.crt
cp your-private-key.key /etc/ssl/certs/ai-dev/server.key
```

2. Restart the service:
```bash
docker-compose -f docker-compose.runpod.yml restart
```

## ⚡ Performance Optimization

### GPU Configuration

```bash
# Enable GPU support
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST=6.0;6.1;7.0;7.5;8.0;8.6

# Memory optimization
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Worker Configuration

```bash
# Adjust based on your GPU memory
WORKERS=4
MAX_WORKERS=8
OMP_NUM_THREADS=4
```

## 🔧 Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   ```bash
   # Regenerate certificates
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout ssl/server.key -out ssl/server.crt \
     -subj "/C=US/ST=State/L=City/O=AI-Dev/CN=localhost"
   ```

2. **Port Access Issues**
   ```bash
   # Check if ports are exposed in RunPod
   # Ensure ports 8000 and 8443 are configured
   ```

3. **API Key Errors**
   ```bash
   # Verify API keys in .env file
   echo $OPENAI_API_KEY
   ```

### Logs

Check application logs:

```bash
# Docker logs
docker-compose -f docker-compose.runpod.yml logs -f

# Application logs
tail -f logs/ai-dev.log
```

## 🛡️ Security Notes

### Self-Signed Certificates

The deployment uses self-signed SSL certificates by default. Browsers will show a security warning. This is normal and safe for development/testing.

### Production Security

For production use:
1. Use valid SSL certificates from a CA
2. Configure proper firewall rules
3. Use environment-specific API keys
4. Enable request rate limiting if needed

## 📞 Support

If you encounter issues:

1. Check the logs for error messages
2. Verify your API keys are correct
3. Ensure RunPod ports are properly exposed
4. Try regenerating SSL certificates

## 🎯 Next Steps

After successful deployment:

1. Test the API endpoints
2. Configure your client applications
3. Set up monitoring and logging
4. Scale workers based on usage

---

**🔓 Remember: This deployment is configured for uncensored operation. Use responsibly and in compliance with applicable laws and regulations.**
