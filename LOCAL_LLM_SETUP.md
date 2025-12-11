# 🧠 Local LLM Setup Guide for OmniVid-Lite

This guide will help you set up a local Large Language Model (LLM) to enhance OmniVid-Lite's video generation capabilities with true AI understanding.

## 🤖 Why Local LLM?

- **Privacy**: No data sent to external APIs
- **Cost**: No usage fees or rate limits
- **Speed**: Once loaded, faster than API calls
- **Offline**: Works without internet connection
- **Control**: Full control over the AI model

## 🚀 Recommended Models

### 1. **DeepSeek-R1 (Recommended)**
```bash
# Pull the model
ollama pull deepseek-r1:7b

# Verify installation
ollama list
```

**Why DeepSeek?**
- Excellent reasoning capabilities
- Good balance of performance and resource usage
- Strong at creative content generation
- Efficient for video scene description

### 2. **Llama 3.1 (Alternative)**
```bash
# Pull Llama 3.1
ollama pull llama3.1:8b

# Or the larger 70B model (requires more RAM)
ollama pull llama3.1:70b
```

### 3. **Mistral (Lightweight Option)**
```bash
# Pull Mistral
ollama pull mistral:7b
```

## 🛠️ Installation Steps

### Step 1: Install Ollama

#### Windows:
1. Download from: https://ollama.ai/download
2. Run the installer
3. Verify: `ollama --version`

#### Linux/macOS:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Start Ollama Service

#### Windows:
- Ollama runs automatically as a service

#### Linux/macOS:
```bash
# Start Ollama (run in background)
ollama serve

# Or run as systemd service
sudo systemctl start ollama
sudo systemctl enable ollama
```

### Step 3: Download Your Chosen Model

```bash
# DeepSeek-R1 (Recommended)
ollama pull deepseek-r1:7b

# Verify model is downloaded
ollama list
```

### Step 4: Configure OmniVid-Lite

Update your `.env` file:

```env
# Enable local LLM
USE_LOCAL_LLM=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b

# Keep OpenAI as fallback (optional)
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4o-mini
```

### Step 5: Test the Setup

1. **Start the backend:**
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Check AI status in the frontend:**
   - Look for the AI status indicator in the header
   - It should show "🤖 AI Available" when working
   - Hover over it for detailed status

3. **Test with a prompt:**
   - Try: "A futuristic city with flying cars"
   - The AI should generate rich scene descriptions instead of just rendering text

## 🔧 Troubleshooting

### Common Issues:

#### 1. **"Model not found" Error**
```bash
# List available models
ollama list

# Pull the correct model
ollama pull deepseek-r1:7b
```

#### 2. **Connection Refused**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

#### 3. **Out of Memory**
- Try smaller models: `deepseek-r1:1.5b` or `mistral:7b`
- Close other applications
- Consider upgrading RAM

#### 4. **Slow First Response**
- First request loads the model into memory (~30-60 seconds)
- Subsequent requests are much faster
- This is normal behavior

### Performance Tuning:

#### For Better Speed:
```bash
# Use smaller, faster models
ollama pull phi3:3.8b
ollama pull llama3.1:8b

# Update .env
OLLAMA_MODEL=phi3:3.8b
```

#### For Better Quality:
```bash
# Use larger models
ollama pull llama3.1:70b
ollama pull deepseek-r1:14b

# Update .env
OLLAMA_MODEL=deepseek-r1:14b
```

## 🎯 Expected Behavior

### With AI Available:
- **Input**: "a cat playing piano"
- **AI Processing**: Generates scene with cat, piano, musical notes, dynamic animation
- **Result**: Rich, animated video with multiple elements

### Without AI (Fallback):
- **Input**: "a cat playing piano"
- **Processing**: Enhances to "🎹 CAT PLAYING PIANO! 🎵 Meow • Keys • Music • HARMONY! 🎹"
- **Result**: Enhanced text animation (still good, but less sophisticated)

## 📊 System Requirements

### Minimum:
- **RAM**: 8GB
- **Storage**: 10GB free space
- **OS**: Windows 10+, Ubuntu 18+, macOS 10.15+

### Recommended:
- **RAM**: 16GB+
- **Storage**: 20GB+ SSD
- **GPU**: NVIDIA GPU with CUDA (optional, speeds up inference)

## 🔄 Switching Between Models

```bash
# Stop current model
ollama stop deepseek-r1:7b

# Start new model
ollama run llama3.1:8b

# Update .env
OLLAMA_MODEL=llama3.1:8b

# Restart OmniVid-Lite
```

## 📈 Monitoring & Logs

- **AI Status**: Check the indicator in the frontend header
- **Logs**: Look for AI-related messages in backend logs
- **Performance**: Monitor response times in the UI

## 🎨 Advanced Configuration

### Custom Model Parameters:
```env
# Model parameters (advanced)
OLLAMA_NUM_CTX=4096
OLLAMA_NUM_THREAD=4
OLLAMA_NUM_GPU=1
```

### Multiple Models:
You can run multiple models and switch between them by updating the `OLLAMA_MODEL` in `.env`.

## 🚨 Emergency Fallback

If local LLM setup fails, the system automatically falls back to intelligent text enhancement, ensuring the application always works.

## 📞 Support

If you encounter issues:
1. Check the AI status indicator in the frontend
2. Review backend logs for error messages
3. Verify Ollama is running: `ollama list`
4. Test Ollama directly: `ollama run deepseek-r1:7b`

---

**🎉 With local LLM configured, your OmniVid-Lite will create truly AI-powered videos with rich scenes, animations, and creative content generation!**