# 🤖 Local AI Setup Guide

This guide will help you set up local AI models for the SAR Drone System without requiring any API keys.

## 🚀 Quick Start

### 1. Automated Setup (Recommended)

Run the automated setup script:

```bash
python setup_local_ai.py
```

This script will:
- Install Ollama if not present
- Download required AI models
- Configure the system for local AI
- Test the setup

### 2. Manual Setup

If you prefer to set up manually:

#### Step 1: Install Ollama

**Linux/macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS (Homebrew):**
```bash
brew install ollama
```

**Windows:**
Download from [https://ollama.ai/download](https://ollama.ai/download)

#### Step 2: Start Ollama Service

```bash
ollama serve
```

#### Step 3: Download AI Models

```bash
# Main model for mission planning
ollama pull llama3.2:3b

# Fallback model for faster responses
ollama pull llama3.2:1b
```

#### Step 4: Test the Setup

```bash
# Test the main model
ollama run llama3.2:3b "Hello, are you working?"

# Test the fallback model
ollama run llama3.2:1b "Hello, are you working?"
```

## 🔧 Configuration

The system is configured to use local models by default. No API keys are required.

### Environment Variables

Create a `.env` file in the project root:

```bash
# Local AI Configuration
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b
FALLBACK_MODEL=llama3.2:1b
AI_MODEL_TIMEOUT=30

# Database
DATABASE_URL=sqlite:///./sar_drone.db

# Security
SECRET_KEY=your-secret-key-change-in-production-make-it-very-long-and-secure

# API
API_HOST=0.0.0.0
API_PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173

# WebSocket
WS_URL=ws://localhost:8000/ws

# Logging
LOG_LEVEL=INFO
DEBUG=True
```

## 🎯 Supported Models

### Primary Models (Recommended)

| Model | Size | Use Case | RAM Required |
|-------|------|----------|--------------|
| `llama3.2:3b` | ~2GB | Mission planning, decision making | 4GB+ |
| `llama3.2:1b` | ~1GB | Fast responses, fallback | 2GB+ |

### Alternative Models

| Model | Size | Use Case | RAM Required |
|-------|------|----------|--------------|
| `llama3.2:8b` | ~5GB | High-quality responses | 8GB+ |
| `llama3.2:70b` | ~40GB | Maximum quality | 40GB+ |
| `mistral:7b` | ~4GB | Alternative to Llama | 6GB+ |
| `codellama:7b` | ~4GB | Code generation | 6GB+ |

## 🚀 Starting the System

### Option 1: Start with AI Setup Check

```bash
python start_ai_system.py
```

This will:
- Check if local AI is properly configured
- Start the backend server
- Start the frontend server
- Provide access URLs

### Option 2: Start System Only

```bash
python start_system.py
```

This starts the system without AI features if local AI is not available.

## 🧪 Testing the AI Integration

Run the comprehensive test suite:

```bash
python test_ai_integration.py
```

This will test:
- Backend health
- AI decision creation
- AI decision approval
- WebSocket connections
- Mission planning integration
- End-to-end workflow

## 🔍 Troubleshooting

### Common Issues

#### 1. Ollama Not Found

**Error:** `ollama: command not found`

**Solution:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Add to PATH (if needed)
export PATH=$PATH:/usr/local/bin
```

#### 2. Ollama Service Not Running

**Error:** `Connection refused` or `Cannot connect to Ollama`

**Solution:**
```bash
# Start Ollama service
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

#### 3. Model Not Found

**Error:** `Model not found` or `Model not available`

**Solution:**
```bash
# List available models
ollama list

# Pull required models
ollama pull llama3.2:3b
ollama pull llama3.2:1b
```

#### 4. Out of Memory

**Error:** `Out of memory` or `CUDA out of memory`

**Solution:**
- Use smaller models (`llama3.2:1b` instead of `llama3.2:3b`)
- Close other applications
- Increase system RAM
- Use CPU instead of GPU

#### 5. Slow Responses

**Issue:** AI responses are very slow

**Solution:**
- Use smaller models
- Reduce `max_tokens` in configuration
- Use GPU acceleration if available
- Increase `AI_MODEL_TIMEOUT` in configuration

### Performance Optimization

#### 1. GPU Acceleration

If you have a compatible GPU:

```bash
# Install CUDA (Linux)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
sudo apt update
sudo apt install cuda

# Install Ollama with GPU support
curl -fsSL https://ollama.ai/install.sh | sh
```

#### 2. Model Optimization

```bash
# Use quantized models for better performance
ollama pull llama3.2:3b-q4_0  # 4-bit quantization
ollama pull llama3.2:1b-q4_0  # 4-bit quantization
```

#### 3. System Configuration

Update `.env` for better performance:

```bash
# Reduce timeout for faster responses
AI_MODEL_TIMEOUT=15

# Use smaller model as default
DEFAULT_MODEL=llama3.2:1b
FALLBACK_MODEL=llama3.2:1b
```

## 📊 Monitoring AI Performance

### 1. Check Model Status

```bash
# List all models
ollama list

# Get model information
ollama show llama3.2:3b

# Test model performance
ollama run llama3.2:3b "Test response time"
```

### 2. Monitor System Resources

```bash
# Check memory usage
htop

# Check GPU usage (if available)
nvidia-smi

# Check disk usage
df -h
```

### 3. API Health Check

```bash
# Check AI service health
curl http://localhost:8000/api/v1/ai-decisions/performance

# Check available models
curl http://localhost:11434/api/tags
```

## 🔒 Security Considerations

### 1. Local Processing

- All AI processing happens locally
- No data is sent to external services
- No API keys required
- Complete privacy and security

### 2. Model Security

- Models are downloaded from official sources
- No custom model modifications
- Regular updates available
- Sandboxed execution

### 3. Network Security

- Ollama runs on localhost only
- No external network access required
- Firewall-friendly configuration
- Isolated from internet

## 🎯 Best Practices

### 1. Model Selection

- Use `llama3.2:3b` for production missions
- Use `llama3.2:1b` for development/testing
- Keep both models available for fallback

### 2. Resource Management

- Monitor memory usage
- Use appropriate model sizes
- Implement proper error handling
- Set reasonable timeouts

### 3. Performance

- Test with your specific hardware
- Optimize for your use case
- Monitor response times
- Implement caching where appropriate

## 📚 Additional Resources

- [Ollama Documentation](https://ollama.ai/docs)
- [Llama 3.2 Models](https://huggingface.co/meta-llama)
- [Model Performance Benchmarks](https://ollama.ai/library)
- [GPU Acceleration Guide](https://ollama.ai/docs/gpu)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run the test suite: `python test_ai_integration.py`
3. Check system logs for detailed error messages
4. Ensure all dependencies are properly installed
5. Verify Ollama is running and accessible

---

**🎉 You're now ready to use the SAR Drone System with local AI!**

The system will automatically use your local models for all AI-powered features including mission planning, decision making, and conversational interfaces.