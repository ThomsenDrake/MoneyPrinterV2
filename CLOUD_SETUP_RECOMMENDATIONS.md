# Cloud Environment Setup Recommendations for MoneyPrinterV2

**Generated:** 2025-11-04
**Purpose:** Optimal cloud configuration for Claude Code sessions working with MoneyPrinterV2

---

## Executive Summary

MoneyPrinterV2 is a Python-based automation suite for content creation (YouTube Shorts, Twitter posting, affiliate marketing, and business outreach). The application requires:
- **Compute-intensive** video processing (MoviePy, CoquiTTS)
- **Browser automation** (Selenium Firefox, headless or GUI mode)
- **AI/LLM integration** (g4f for free GPT-4 access)
- **External API calls** (AssemblyAI, SMTP)
- **Persistent storage** for models, cache, and secrets

---

## 1. Recommended Cloud Platform Options

### Option A: Ubuntu 22.04 LTS VM (Preferred)
**Best for:** Full feature support, scheduled jobs, production use

**Specifications:**
- **OS:** Ubuntu 22.04 LTS (amd64)
- **CPU:** 4+ vCPU (for video processing parallelization)
- **RAM:** 8-16 GB (CoquiTTS models + MoviePy + Firefox)
- **Storage:** 50-100 GB SSD
  - 10 GB: OS and system packages
  - 5 GB: Python dependencies
  - 5-10 GB: CoquiTTS models (downloaded on first run)
  - 5-10 GB: Songs/music library
  - 10-20 GB: Working directory for video generation
  - 10-20 GB: Headroom for cache and temporary files

**Cloud Providers:**
- **AWS EC2:** t3.xlarge (4 vCPU, 16 GB RAM)
- **Google Cloud:** e2-standard-4 (4 vCPU, 16 GB RAM)
- **Azure:** Standard_D4s_v3 (4 vCPU, 16 GB RAM)
- **DigitalOcean:** Premium Intel 4 vCPU / 8 GB RAM
- **Linode:** Dedicated 8GB (4 vCPU, 8 GB RAM)

**Advantages:**
- Full control over environment
- Supports headless and GUI Firefox (with VNC)
- Can run scheduled CRON jobs natively
- Persistent storage for Firefox profiles
- Suitable for long-running automation tasks

---

### Option B: Docker Container Environment
**Best for:** Reproducible builds, CI/CD, local development

**Specifications:**
- **Base Image:** `python:3.9-slim-bullseye` or `ubuntu:22.04`
- **Required System Packages:**
  ```
  firefox-esr, wget, xvfb (for headless), imagemagick,
  fonts-liberation, ffmpeg, gcc, build-essential
  ```
- **Container Resources:**
  - CPU: 4 cores
  - Memory: 8-16 GB
  - Storage: 50 GB volume

**Dockerfile Structure (Example):**
```dockerfile
FROM python:3.9-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    xvfb \
    imagemagick \
    fonts-liberation \
    ffmpeg \
    gcc \
    g++ \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install GeckoDriver
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.33.0-linux64.tar.gz -C /usr/local/bin \
    && rm geckodriver-v0.33.0-linux64.tar.gz

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for headless mode
ENV DISPLAY=:99
ENV IMAGEMAGICK_BINARY=/usr/bin/convert

COPY . .
CMD ["python", "src/main.py"]
```

**Advantages:**
- Portable across any Docker-capable platform
- Reproducible environment
- Easy local testing

**Limitations:**
- Requires persistent volumes for config.json and .mp/ cache
- Firefox profiles need to be mounted or baked in

---

### Option C: GitHub Codespaces (Development Only)
**Best for:** Quick testing, code editing, non-production experiments

**Specifications:**
- **Machine Type:** 4-core, 8 GB RAM minimum
- **Prebuild Configuration:** `.devcontainer/devcontainer.json`

**Limitations:**
- Not suitable for scheduled automation (hourly quotas)
- Ephemeral storage (requires Git commits for persistence)
- Cannot run 24/7 CRON jobs
- Browser automation may require headless mode only

---

## 2. Required System Dependencies

### Core Runtime
```bash
# Python 3.9+
python3.9 python3.9-venv python3.9-dev

# Firefox (for Selenium)
firefox-esr  # or firefox

# GeckoDriver (auto-downloaded by webdriver_manager, but can pre-install)
# See: https://github.com/mozilla/geckodriver/releases

# ImageMagick (required by MoviePy)
imagemagick

# FFmpeg (video processing)
ffmpeg

# Build tools (for CoquiTTS compilation)
gcc g++ build-essential

# Fonts (for subtitle rendering)
fonts-liberation ttf-mscorefonts-installer
```

### Optional (for specific features)
```bash
# Go language (for Google Maps scraper - only if using Outreach feature)
golang-go

# Xvfb (for headless Firefox with GUI simulation)
xvfb x11vnc

# VNC server (if you want to view Firefox GUI remotely)
tightvncserver
```

---

## 3. Environment Configuration

### Environment Variables
```bash
# Display for headless Firefox
export DISPLAY=:99

# ImageMagick binary path (Linux)
export IMAGEMAGICK_BINARY=/usr/bin/convert

# Optional: Increase ulimit for file handles
ulimit -n 4096
```

### config.json Settings for Cloud
```json
{
  "verbose": true,
  "firefox_profile": "/app/.mozilla/firefox/your-profile.default",
  "headless": true,  // Set to true for cloud environments
  "twitter_language": "English",
  "llm": "gpt4",
  "image_prompt_llm": "gpt35_turbo",
  "image_model": "prodia",
  "threads": 4,  // Match CPU cores
  "zip_url": "",  // Optional: URL to custom songs
  "is_for_kids": false,
  "google_maps_scraper": "https://github.com/gosom/google-maps-scraper/archive/refs/tags/v0.9.7.zip",
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "YOUR_EMAIL@gmail.com",
    "password": "YOUR_APP_PASSWORD"  // Use App Passwords, not real password
  },
  "google_maps_scraper_niche": "",
  "scraper_timeout": 300,
  "outreach_message_subject": "I have a question...",
  "outreach_message_body_file": "outreach_message.html",
  "assembly_ai_api_key": "YOUR_ASSEMBLYAI_KEY",
  "font": "bold_font.ttf",
  "imagemagick_path": "/usr/bin/convert",
  "script_sentence_length": 4
}
```

---

## 4. Persistent Storage Requirements

### Directory Structure
```
/app/MoneyPrinterV2/
├── config.json           # PERSIST - Contains secrets
├── .mp/                  # PERSIST - Cache directory
│   ├── youtube.json      # Account data
│   ├── twitter.json      # Account data
│   ├── afm.json          # Products
│   └── scraper_results.csv
├── .mozilla/             # PERSIST - Firefox profiles (if using)
│   └── firefox/
│       └── your-profile.default/
├── Songs/                # PERSIST - Music library (if downloaded)
└── .cache/               # OPTIONAL PERSIST - Downloaded models
    └── tts/              # CoquiTTS models (~500 MB)
```

### Volume Mounts (Docker Example)
```bash
docker run -v /host/config:/app/config \
           -v /host/cache:/app/.mp \
           -v /host/firefox:/app/.mozilla \
           -v /host/models:/root/.local/share/tts \
           moneyprinterv2
```

---

## 5. Network & Security Requirements

### Outbound Network Access
- **g4f API endpoints** (various free LLM/image providers)
- **AssemblyAI API:** `api.assemblyai.com` (port 443)
- **YouTube:** `youtube.com`, `accounts.google.com` (port 443)
- **Twitter:** `twitter.com`, `x.com` (port 443)
- **Amazon:** `amazon.com` (port 443, for scraping)
- **SMTP:** `smtp.gmail.com` (port 587, TLS)
- **GitHub:** For downloading Go scraper, songs (port 443)

### Security Best Practices
1. **Never commit config.json** (already in .gitignore)
2. **Use environment variables** for secrets (optional improvement)
3. **Gmail App Passwords:** Use Google App Passwords, not real passwords
4. **AssemblyAI API Key:** Store securely, rotate regularly
5. **Firefox Profiles:** Backup regularly, contain logged-in sessions
6. **Network Firewall:** Only allow outbound HTTPS (443), SMTP (587)

### Secrets Management (Recommended)
```bash
# Use secret manager instead of config.json
export ASSEMBLYAI_API_KEY="xxx"
export GMAIL_USERNAME="xxx"
export GMAIL_PASSWORD="xxx"

# Modify config.py to read from env vars as fallback
```

---

## 6. Resource Usage Estimates

### CPU Usage
- **Idle:** 0.5-1% (waiting for user input)
- **Video Generation:**
  - Script generation (g4f): 5-10% (network-bound)
  - Image generation: 10-20%
  - TTS (CoquiTTS): 80-100% per core (5-30 seconds per video)
  - Video composition (MoviePy): 60-80% per core (30-60 seconds)
- **Browser Automation:** 20-40% (Firefox)

### Memory Usage
- **Base Python Process:** 200-500 MB
- **CoquiTTS Models Loaded:** 500 MB - 1.5 GB
- **MoviePy Video Processing:** 1-3 GB
- **Firefox Instance:** 500 MB - 1 GB
- **Peak Usage:** 4-6 GB (during video generation)

### Storage I/O
- **Model Downloads (first run):**
  - CoquiTTS models: 500 MB - 1 GB
  - Songs ZIP (optional): 50-500 MB
  - Google Maps scraper: 20 MB
- **Per Video Generated:**
  - Images: 5-10 MB
  - Audio (TTS): 1-5 MB
  - Final video: 10-50 MB
- **Cache Growth:** 100-500 MB per 100 videos

### Network Bandwidth
- **Typical Usage:** 50-200 MB per video (including uploads)
- **Monthly Estimate:** 5-20 GB for moderate use

---

## 7. Recommended Cloud Setup (Step-by-Step)

### For AWS EC2 (Ubuntu 22.04)

```bash
# 1. Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \  # Ubuntu 22.04 LTS
  --instance-type t3.xlarge \
  --key-name your-key \
  --security-group-ids sg-xxxx \
  --subnet-id subnet-xxxx \
  --block-device-mappings DeviceName=/dev/sda1,Ebs={VolumeSize=100}

# 2. SSH into instance
ssh -i your-key.pem ubuntu@<instance-ip>

# 3. Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  python3.9 python3.9-venv python3.9-dev \
  firefox-esr wget git \
  imagemagick ffmpeg \
  gcc g++ build-essential \
  fonts-liberation \
  xvfb

# 4. Clone repository
git clone https://github.com/FujiwaraChoki/MoneyPrinterV2.git
cd MoneyPrinterV2

# 5. Setup Python environment
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Configure application
cp config.example.json config.json
nano config.json  # Fill in your API keys and settings

# 7. (Optional) Setup Firefox profile
firefox -CreateProfile "automation /home/ubuntu/.mozilla/firefox/automation.default"
# Manually login to YouTube/Twitter, then copy profile path to config.json

# 8. Test run
python src/main.py

# 9. (Optional) Setup systemd service for CRON jobs
# See Section 8 below
```

---

## 8. Scheduled Automation Setup

### Systemd Service (for CRON jobs)

Create `/etc/systemd/system/moneyprinter-youtube.service`:
```ini
[Unit]
Description=MoneyPrinter YouTube Automation
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/MoneyPrinterV2
Environment="PATH=/home/ubuntu/MoneyPrinterV2/venv/bin"
Environment="DISPLAY=:99"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 &
ExecStart=/home/ubuntu/MoneyPrinterV2/venv/bin/python src/cron.py youtube <account-uuid>
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable moneyprinter-youtube.service
sudo systemctl start moneyprinter-youtube.service
sudo systemctl status moneyprinter-youtube.service
```

---

## 9. Monitoring & Maintenance

### Log Monitoring
```bash
# Application logs
tail -f /home/ubuntu/MoneyPrinterV2/logs/*.log  # If implemented

# System logs
journalctl -u moneyprinter-youtube.service -f

# Disk usage
df -h
du -sh /home/ubuntu/MoneyPrinterV2/.mp
```

### Cleanup Cron Job
```bash
# Add to crontab to clean temp files daily
crontab -e

# Clean temporary files daily at 3 AM
0 3 * * * cd /home/ubuntu/MoneyPrinterV2 && find .mp/temp -type f -mtime +1 -delete
```

### Resource Monitoring
```bash
# Install htop
sudo apt install htop

# Monitor real-time usage
htop

# Check GPU (if using GPU-enabled instance)
nvidia-smi  # For CUDA-enabled instances
```

---

## 10. Troubleshooting Common Issues

### Issue: Firefox crashes in headless mode
**Solution:**
```bash
# Use Xvfb for virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

### Issue: CoquiTTS model download fails
**Solution:**
```bash
# Pre-download models manually
python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('tts_models/en/ljspeech/tacotron2-DDC_ph')"
```

### Issue: ImageMagick "not authorized" error
**Solution:**
```bash
# Edit ImageMagick policy
sudo nano /etc/ImageMagick-6/policy.xml

# Change this line:
# <policy domain="path" rights="none" pattern="@*"/>
# To:
# <policy domain="path" rights="read|write" pattern="@*"/>
```

### Issue: Out of memory during video processing
**Solution:**
```bash
# Reduce threads in config.json
"threads": 2  # Instead of 4

# Or add swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 11. Cost Estimates (Monthly)

### AWS EC2 (t3.xlarge, us-east-1)
- **Compute (730 hrs):** $121.76
- **Storage (100 GB SSD):** $10.00
- **Network (10 GB out):** $0.90
- **Total:** ~$133/month

### Google Cloud (e2-standard-4, us-central1)
- **Compute (730 hrs):** $97.09
- **Storage (100 GB SSD):** $17.00
- **Network (10 GB out):** $1.20
- **Total:** ~$115/month

### DigitalOcean (Premium Intel 4 vCPU)
- **Droplet:** $84/month (includes 100 GB SSD)
- **Network:** Included (1 TB)
- **Total:** ~$84/month

### Linode (Dedicated 8GB)
- **Compute:** $60/month (includes 160 GB SSD)
- **Network:** Included (4 TB)
- **Total:** ~$60/month **(MOST COST-EFFECTIVE)**

---

## 12. Final Recommendations

### For Claude Code Sessions

**Recommended Setup:**
1. **Platform:** Ubuntu 22.04 LTS VM (Linode Dedicated 8GB for cost, AWS for scalability)
2. **Storage:** 100 GB SSD with daily backups
3. **Persistence:** Mount volumes for `config.json`, `.mp/`, `.mozilla/`, `.cache/`
4. **Network:** Ensure outbound HTTPS (443) and SMTP (587) access
5. **Configuration:**
   - Set `headless: true` in config.json
   - Set `threads: 4` to match CPU cores
   - Pre-configure Firefox profiles and upload to instance
   - Store secrets in environment variables or AWS Secrets Manager

**For Quick Testing (Claude Code):**
- Use GitHub Codespaces with 4-core machine
- Set `headless: true`
- Understand it's ephemeral (commit changes frequently)
- Avoid scheduled jobs (run manually)

**For Production Automation:**
- Use dedicated Ubuntu VM (Linode/DigitalOean)
- Setup systemd services for scheduled tasks
- Enable automated backups (config.json, .mp/, Firefox profiles)
- Monitor disk usage and set up log rotation

---

## 13. Security Checklist

- [ ] `config.json` never committed to Git (.gitignore verified)
- [ ] AssemblyAI API key stored securely
- [ ] Gmail using App Password, not real password
- [ ] Firefox profiles backed up separately
- [ ] Instance firewall allows only outbound 443, 587
- [ ] SSH key-based authentication (no password login)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] VPN or IP whitelist for SSH access (optional)
- [ ] Secrets rotated every 90 days

---

## 14. Summary Table

| Requirement | Specification |
|-------------|---------------|
| **OS** | Ubuntu 22.04 LTS (amd64) |
| **CPU** | 4 vCPU minimum |
| **RAM** | 8-16 GB |
| **Storage** | 100 GB SSD |
| **Python** | 3.9+ |
| **Browser** | Firefox ESR + GeckoDriver |
| **Display** | Xvfb for headless (DISPLAY=:99) |
| **Persistent Volumes** | config.json, .mp/, .mozilla/, .cache/tts/ |
| **Network** | HTTPS (443), SMTP (587) outbound |
| **Cost** | $60-135/month (depending on provider) |
| **Best Value** | Linode Dedicated 8GB ($60/month) |

---

## 15. Quick Start Commands

```bash
# Complete setup script for Ubuntu 22.04
#!/bin/bash
set -e

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
  python3.9 python3.9-venv python3.9-dev \
  firefox-esr wget git \
  imagemagick ffmpeg \
  gcc g++ build-essential \
  fonts-liberation xvfb

# Clone repository
cd ~
git clone https://github.com/FujiwaraChoki/MoneyPrinterV2.git
cd MoneyPrinterV2

# Setup Python environment
python3.9 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create config from example
cp config.example.json config.json

echo "Setup complete! Edit config.json with your settings, then run:"
echo "  source venv/bin/activate"
echo "  python src/main.py"
```

---

**Document Maintained By:** Claude Code Analysis
**Last Updated:** 2025-11-04
**Version:** 1.0
