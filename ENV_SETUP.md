# Environment Variables Setup Guide

This guide explains how to use environment variables with MoneyPrinterV2 for better security and cloud deployment.

---

## Why Use Environment Variables?

**Security Benefits:**
- **No secrets in Git**: API keys and passwords never accidentally committed
- **Easier rotation**: Change secrets without modifying config files
- **Cloud-native**: Works seamlessly with Docker, Kubernetes, CI/CD
- **Multiple environments**: Easy to have dev/staging/prod configurations

**Current Status:**
- MoneyPrinterV2 currently uses `config.json` for all configuration
- This guide provides a migration path to environment variables
- Both methods can coexist during transition

---

## Quick Start

### 1. Create Your .env File

```bash
# Copy the example file
cp .env.example .env

# Edit with your secrets (use nano, vim, or any editor)
nano .env
```

### 2. Required Variables (Minimum Setup)

Fill in these critical variables in your `.env` file:

```bash
# Essential for subtitle generation
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

# Essential for email outreach (use App Password, not real password!)
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your_16_char_app_password

# Essential for cloud environments
HEADLESS=true
IMAGEMAGICK_PATH=/usr/bin/convert
```

### 3. Load Environment Variables

**Option A: Using python-dotenv (Recommended)**

Install python-dotenv:
```bash
pip install python-dotenv
```

Load in your Python scripts:
```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Access variables
api_key = os.getenv('ASSEMBLYAI_API_KEY')
```

**Option B: Export in Shell (Linux/macOS)**

```bash
# Load all variables into current shell
export $(cat .env | xargs)

# Or add to your ~/.bashrc or ~/.zshrc for persistence
source .env
```

**Option C: Docker/Docker Compose**

```yaml
# docker-compose.yml
services:
  moneyprinter:
    build: .
    env_file:
      - .env
    volumes:
      - ./config:/app/config
```

---

## Complete Environment Variables Reference

### Critical Secrets

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `ASSEMBLYAI_API_KEY` | AssemblyAI API key for speech-to-text | `abc123...` | Yes (for subtitles) |
| `SMTP_USERNAME` | Gmail/SMTP username | `you@gmail.com` | Yes (for outreach) |
| `SMTP_PASSWORD` | Gmail App Password (NOT real password!) | `abcd efgh ijkl mnop` | Yes (for outreach) |

### General Configuration

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `VERBOSE` | Enable debug logging | `true` | `true`, `false` |
| `FIREFOX_PROFILE` | Path to Firefox profile | `` (empty) | `/path/to/profile` |
| `HEADLESS` | Run Firefox without GUI | `false` | `true`, `false` |

### AI/LLM Configuration

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `LLM_MODEL` | Main LLM for content | `gpt4` | `gpt4`, `gpt35_turbo`, `llama2_*`, `mixtral_8x7b` |
| `IMAGE_PROMPT_LLM` | LLM for image prompts | `gpt35_turbo` | Same as above |
| `IMAGE_MODEL` | Image generation model | `prodia` | `prodia`, `lexica`, `v1`, `v2`, `v3`, `turbo` |

### Social Media

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `TWITTER_LANGUAGE` | Tweet language | `English` | Any language |
| `IS_FOR_KIDS` | Mark YouTube as kid-friendly | `false` | `true`, `false` |

### Performance

| Variable | Description | Default | Recommendation |
|----------|-------------|---------|----------------|
| `THREADS` | CPU threads for video processing | `2` | Set to CPU core count |

### Email Outreach

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_SERVER` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `GOOGLE_MAPS_SCRAPER_NICHE` | Business category to scrape | `` (empty) |
| `SCRAPER_TIMEOUT` | Scraper timeout in seconds | `300` |
| `OUTREACH_MESSAGE_SUBJECT` | Email subject | `I have a question...` |
| `OUTREACH_MESSAGE_BODY_FILE` | HTML email body file | `outreach_message.html` |

### Video/Subtitle Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `FONT` | Font file for subtitles | `bold_font.ttf` |
| `IMAGEMAGICK_PATH` | ImageMagick binary path | `/usr/bin/convert` |
| `SCRIPT_SENTENCE_LENGTH` | Words per subtitle | `4` |

### External Resources

| Variable | Description | Default |
|----------|-------------|---------|
| `ZIP_URL` | Custom music ZIP URL | `` (empty) |
| `GOOGLE_MAPS_SCRAPER_URL` | Google Maps scraper URL | GitHub release link |

---

## Security Best Practices

### 1. Gmail App Passwords (CRITICAL!)

**Never use your real Gmail password!** Use App Passwords instead:

1. Go to https://myaccount.google.com/apppasswords
2. Sign in to your Google Account
3. Click "Select app" → Choose "Mail"
4. Click "Select device" → Choose "Other"
5. Enter "MoneyPrinterV2" as the name
6. Click "Generate"
7. Copy the 16-character password (format: `abcd efgh ijkl mnop`)
8. Use this in `SMTP_PASSWORD` variable

**Why?** App Passwords:
- Can be revoked without changing your main password
- Work even with 2FA enabled
- Limit access to only email (not entire Google account)
- Are more secure for automated scripts

### 2. AssemblyAI API Key

1. Sign up at https://www.assemblyai.com/
2. Free tier: 5 hours of audio per month
3. Copy your API key from the dashboard
4. Store in `ASSEMBLYAI_API_KEY` variable

**Best practices:**
- Rotate every 90 days
- Use separate keys for dev/prod
- Monitor usage in AssemblyAI dashboard

### 3. File Permissions

Protect your `.env` file from unauthorized access:

```bash
# Linux/macOS: Make .env readable only by you
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (owner read/write only)
```

### 4. Never Commit Secrets

The `.gitignore` file already excludes:
- `.env`
- `.env.local`
- `config.json`

**Double-check before committing:**
```bash
# Check what will be committed
git status

# If .env appears, DO NOT commit! Add to .gitignore immediately
echo ".env" >> .gitignore
```

### 5. Cloud Deployment Secrets

**For production use, use cloud secret managers:**

**AWS:**
```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name moneyprinter/assemblyai-key \
  --secret-string "your_api_key"

# Or use AWS Systems Manager Parameter Store
aws ssm put-parameter \
  --name /moneyprinter/assemblyai-key \
  --value "your_api_key" \
  --type SecureString
```

**Google Cloud:**
```bash
# Store in Google Secret Manager
gcloud secrets create assemblyai-key --data-file=-
# Enter your API key, then Ctrl+D

# Access in code
gcloud secrets versions access latest --secret="assemblyai-key"
```

**Azure:**
```bash
# Store in Azure Key Vault
az keyvault secret set \
  --vault-name MyKeyVault \
  --name assemblyai-key \
  --value "your_api_key"
```

---

## Migration Guide: config.json → .env

### Current Approach (config.json)

```json
{
  "verbose": true,
  "assembly_ai_api_key": "abc123...",
  "email": {
    "username": "user@gmail.com",
    "password": "dangerous_plaintext_password"
  }
}
```

**Problems:**
- Secrets in plaintext file
- Easy to accidentally commit
- Hard to manage multiple environments

### Recommended Approach (.env + config.json)

**Step 1: Move secrets to .env**

```bash
# .env (git-ignored)
ASSEMBLYAI_API_KEY=abc123...
SMTP_USERNAME=user@gmail.com
SMTP_PASSWORD=app_password_here
```

**Step 2: Keep non-secrets in config.json**

```json
{
  "verbose": true,
  "llm": "gpt4",
  "threads": 4,
  "headless": true
}
```

**Step 3: Modify src/config.py to check .env first**

```python
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def get_assemblyai_api_key() -> str:
    # Check environment variable first, fall back to config.json
    env_key = os.getenv('ASSEMBLYAI_API_KEY')
    if env_key:
        return env_key

    # Fallback to config.json
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["assembly_ai_api_key"]
```

### Hybrid Approach (During Migration)

You can use both simultaneously:
1. Secrets in `.env` (takes precedence)
2. Configuration in `config.json` (fallback)

This allows gradual migration without breaking existing setups.

---

## Testing Your Setup

### 1. Verify .env is Loaded

```bash
# Create test script: test_env.py
cat > test_env.py << 'EOF'
from dotenv import load_dotenv
import os

load_dotenv()

print("Testing environment variables...")
print(f"ASSEMBLYAI_API_KEY: {'✓ Set' if os.getenv('ASSEMBLYAI_API_KEY') else '✗ Missing'}")
print(f"SMTP_USERNAME: {'✓ Set' if os.getenv('SMTP_USERNAME') else '✗ Missing'}")
print(f"SMTP_PASSWORD: {'✓ Set' if os.getenv('SMTP_PASSWORD') else '✗ Missing'}")
print(f"LLM_MODEL: {os.getenv('LLM_MODEL', 'Not set')}")
print(f"HEADLESS: {os.getenv('HEADLESS', 'Not set')}")
EOF

# Run test
python test_env.py
```

### 2. Verify No Secrets in Git

```bash
# Check git history for leaked secrets
git log --all --full-history -- .env
# Should return: "fatal: ambiguous argument '.env': unknown revision"

# Scan for potential secrets (install git-secrets first)
git secrets --scan
```

### 3. Test Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run application
python src/main.py
```

---

## Docker Integration

### Dockerfile with .env Support

```dockerfile
FROM python:3.9-bullseye

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt python-dotenv

# Copy application
COPY . .

# .env should be mounted at runtime, not copied
# NEVER: COPY .env .

CMD ["python", "src/main.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  moneyprinter:
    build: .
    env_file:
      - .env  # Load environment variables
    volumes:
      - ./config.json:/app/config.json:ro  # Read-only config
      - ./.mp:/app/.mp  # Persistent cache
      - ./.mozilla:/app/.mozilla  # Firefox profiles
    environment:
      - DISPLAY=:99  # Additional env vars
      - HEADLESS=true
```

### Running with Docker

```bash
# Build image
docker build -t moneyprinter:latest .

# Run with .env file
docker run --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/.mp:/app/.mp \
  moneyprinter:latest

# Or use docker-compose
docker-compose up
```

---

## Kubernetes Secrets

For production Kubernetes deployments:

### Create Secret from .env

```bash
# Create Kubernetes secret from .env file
kubectl create secret generic moneyprinter-secrets \
  --from-env-file=.env \
  --namespace=default
```

### Use in Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: moneyprinter
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: moneyprinter
        image: moneyprinter:latest
        envFrom:
          - secretRef:
              name: moneyprinter-secrets
        env:
          - name: HEADLESS
            value: "true"
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy MoneyPrinter

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Create .env from secrets
        run: |
          echo "ASSEMBLYAI_API_KEY=${{ secrets.ASSEMBLYAI_API_KEY }}" >> .env
          echo "SMTP_USERNAME=${{ secrets.SMTP_USERNAME }}" >> .env
          echo "SMTP_PASSWORD=${{ secrets.SMTP_PASSWORD }}" >> .env
          echo "HEADLESS=true" >> .env

      - name: Deploy
        run: |
          # Your deployment commands here
          scp .env user@server:/app/.env
```

### GitLab CI

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  script:
    - echo "ASSEMBLYAI_API_KEY=$ASSEMBLYAI_API_KEY" >> .env
    - echo "SMTP_USERNAME=$SMTP_USERNAME" >> .env
    - echo "SMTP_PASSWORD=$SMTP_PASSWORD" >> .env
    # Deploy to server
  only:
    - main
```

---

## Troubleshooting

### Issue: Environment variables not loading

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check file contents (be careful not to expose in logs!)
cat .env  # Only in secure terminal!

# Install python-dotenv if missing
pip install python-dotenv

# Load manually in Python
from dotenv import load_dotenv
load_dotenv(verbose=True)  # Shows debug output
```

### Issue: Gmail SMTP authentication fails

**Common causes:**
1. Using real password instead of App Password
2. 2FA not enabled (required for App Passwords)
3. "Less secure app access" disabled (legacy)

**Solution:**
```bash
# Generate new App Password
1. Enable 2FA: https://myaccount.google.com/signinoptions/two-step-verification
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character password (no spaces in .env)
```

### Issue: Docker can't find .env

**Solution:**
```bash
# Ensure .env is in same directory as docker-compose.yml
ls -la .env docker-compose.yml

# Or specify path explicitly
docker run --env-file /absolute/path/to/.env ...
```

### Issue: Variables empty/undefined

**Check precedence:**
1. System environment variables (highest priority)
2. .env file
3. config.json (fallback)

```bash
# Unset system variable if conflicting
unset ASSEMBLYAI_API_KEY

# Or use .env.local (higher priority than .env)
cp .env .env.local
```

---

## Summary Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Fill in `ASSEMBLYAI_API_KEY`
- [ ] Fill in `SMTP_USERNAME` and `SMTP_PASSWORD` (use App Password!)
- [ ] Set `HEADLESS=true` for cloud environments
- [ ] Set `IMAGEMAGICK_PATH` for your OS
- [ ] Set `THREADS` to match CPU cores
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test with `python test_env.py`
- [ ] Set file permissions: `chmod 600 .env`
- [ ] Never commit `.env` to Git
- [ ] Use cloud secret manager for production
- [ ] Rotate secrets every 90 days

---

**Related Documentation:**
- [CLOUD_SETUP_RECOMMENDATIONS.md](CLOUD_SETUP_RECOMMENDATIONS.md) - Cloud deployment guide
- [docs/Configuration.md](docs/Configuration.md) - Original configuration docs
- [config.example.json](config.example.json) - JSON configuration template

**Last Updated:** 2025-11-04
