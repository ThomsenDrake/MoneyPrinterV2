# Configuration Guide

This document explains how to configure MoneyPrinterV2, including the configuration hierarchy, available options, and best practices.

---

## 📋 Table of Contents

1. [Configuration Hierarchy](#configuration-hierarchy)
2. [Configuration Files](#configuration-files)
3. [Available Settings](#available-settings)
4. [Environment Variables](#environment-variables)
5. [Examples](#examples)
6. [Default Values](#default-values)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)

---

## Configuration Hierarchy

MoneyPrinterV2 uses a **3-tier configuration hierarchy** with clear precedence:

```
1. Environment Variables (highest priority)
   ↓
2. config.json values
   ↓
3. Default values from constants.py (lowest priority)
```

### How It Works

When the application needs a configuration value, it checks sources in this order:

```python
# Example: Getting the verbose flag
1. Check VERBOSE environment variable
   └─ If set: use this value
2. Check config.json "verbose" key
   └─ If exists: use this value
3. Use default from constants.py
   └─ DEFAULT_VERBOSE = False
```

### Benefits

- **Flexibility:** Override any setting without editing files
- **Security:** Keep secrets in environment variables (never in git)
- **Deployment:** Different configs for dev/staging/production
- **Backward Compatibility:** Existing config.json files continue to work

---

## Configuration Files

### config.json

**Location:** Project root directory
**Purpose:** Application settings and non-secret configuration
**Format:** JSON

**Example:**
```json
{
  "verbose": true,
  "headless": false,
  "firefox_profile": "/path/to/firefox/profile",
  "llm": "mistral-medium-latest",
  "image_model": "dall-e-3",
  "threads": 4,
  "script_sentence_length": 4,
  "is_for_kids": false,
  "twitter_language": "en",
  "scraper_timeout": 300
}
```

### .env File

**Location:** Project root directory
**Purpose:** Secret values (API keys, credentials)
**Format:** KEY=VALUE pairs

**Example:**
```bash
# API Keys
MISTRAL_API_KEY=your-mistral-api-key-here
VENICE_API_KEY=your-venice-api-key-here
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here

# Application Settings (overrides config.json)
VERBOSE=true
HEADLESS=true
FIREFOX_PROFILE=/path/to/profile

# Email/SMTP Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**⚠️ Important:** Never commit `.env` to git! It's already in `.gitignore`.

### .env.example

**Location:** Project root directory
**Purpose:** Template showing all available environment variables
**Usage:** Copy to `.env` and fill in your values

```bash
cp .env.example .env
# Edit .env with your actual values
```

---

## Available Settings

### General Application Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `verbose` | bool | `false` | Enable detailed logging output |
| `headless` | bool | `false` | Run browser in headless mode (no GUI) |
| `threads` | int | `1` | Number of threads for video processing (1-32) |

**Environment Variables:**
- `VERBOSE=true` or `VERBOSE=false`
- `HEADLESS=true` or `HEADLESS=false`

---

### Browser Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `firefox_profile` | string | *(required)* | Path to Firefox profile directory |

**Environment Variable:**
- `FIREFOX_PROFILE=/path/to/profile`

**⚠️ Important:** Firefox profile path is **required**. Application won't start without it.

---

### AI/LLM Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `llm` | string | `""` | LLM model to use for text generation |
| `mistral_api_key` | string | `""` | Mistral AI API key *(prefer env var)* |
| `venice_api_key` | string | `""` | Venice AI API key *(prefer env var)* |
| `image_model` | string | `""` | Image generation model |
| `image_prompt_llm` | string | `""` | LLM for generating image prompts |

**Environment Variables (Recommended):**
```bash
MISTRAL_API_KEY=sk-...
VENICE_API_KEY=...
```

**See:** [SECRETS_MANAGEMENT.md](../SECRETS_MANAGEMENT.md) for detailed API key setup.

---

### Content Generation

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `script_sentence_length` | int | `4` | Target number of sentences in generated scripts (1-20) |
| `is_for_kids` | bool | `false` | Mark YouTube content as "made for kids" |
| `twitter_language` | string | `"en"` | Language code for Twitter content |

---

### Media Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `font` | string | `""` | Font file for video subtitles (filename only) |
| `imagemagick_path` | string | `""` | Path to ImageMagick binary |
| `zip_url` | string | *(see defaults)* | URL to download background music |

**Security Note:** `font` and `imagemagick_path` are validated to prevent directory traversal attacks.

---

### Scraper Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `scraper_timeout` | int | `300` | Timeout for scraper operations in seconds (30-3600) |
| `google_maps_scraper` | string | `""` | URL to Google Maps scraper |
| `google_maps_scraper_niche` | string | `""` | Niche/category for scraping |

---

### Outreach Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `outreach_message_subject` | string | `""` | Email subject line for outreach |
| `outreach_message_body_file` | string | `""` | Path to email body template file |

---

### Email/SMTP Configuration

**Recommended:** Use environment variables for email credentials.

**Environment Variables:**
```bash
SMTP_SERVER=smtp.gmail.com        # Default if not set
SMTP_PORT=587                      # Default if not set
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**config.json (alternative):**
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-password"
  }
}
```

**⚠️ Warning:** Storing passwords in config.json is **not recommended**. Use environment variables instead.

---

## Environment Variables

### Complete List

| Variable | Type | Config Key | Default |
|----------|------|------------|---------|
| `VERBOSE` | bool | `verbose` | `false` |
| `HEADLESS` | bool | `headless` | `false` |
| `FIREFOX_PROFILE` | string | `firefox_profile` | - |
| `MISTRAL_API_KEY` | string | `mistral_api_key` | `""` |
| `VENICE_API_KEY` | string | `venice_api_key` | `""` |
| `ASSEMBLYAI_API_KEY` | string | `assembly_ai_api_key` | `""` |
| `SMTP_SERVER` | string | `email.smtp_server` | `smtp.gmail.com` |
| `SMTP_PORT` | int | `email.smtp_port` | `587` |
| `SMTP_USERNAME` | string | `email.username` | `""` |
| `SMTP_PASSWORD` | string | `email.password` | `""` |

### Boolean Values

Boolean environment variables accept multiple formats:

**True values:** `true`, `1`, `yes`, `True`, `YES`
**False values:** `false`, `0`, `no`, `False`, `NO`, *(empty/unset)*

```bash
# All of these enable verbose mode
VERBOSE=true
VERBOSE=1
VERBOSE=yes
```

---

## Examples

### Example 1: Local Development

**.env:**
```bash
VERBOSE=true
HEADLESS=false
FIREFOX_PROFILE=/Users/yourname/Library/Application Support/Firefox/Profiles/abc123.default
MISTRAL_API_KEY=sk-your-key-here
```

**config.json:**
```json
{
  "llm": "mistral-medium-latest",
  "threads": 4,
  "script_sentence_length": 6
}
```

**Result:**
- Verbose logging enabled (env var)
- Browser visible (env var)
- Uses specified Firefox profile (env var)
- Mistral API key secure (env var)
- Other settings from config.json

---

### Example 2: Production Server

**.env:**
```bash
HEADLESS=true
VERBOSE=false
FIREFOX_PROFILE=/opt/firefox-profile
MISTRAL_API_KEY=sk-prod-key
VENICE_API_KEY=vn-prod-key
ASSEMBLYAI_API_KEY=aa-prod-key
```

**config.json:**
```json
{
  "llm": "mistral-large-latest",
  "threads": 8,
  "scraper_timeout": 600,
  "is_for_kids": false
}
```

**Result:**
- Headless browser (no GUI overhead)
- Minimal logging
- All secrets in environment
- Production-optimized settings

---

### Example 3: CI/CD Testing

**.env:**
```bash
HEADLESS=true
VERBOSE=true
FIREFOX_PROFILE=/tmp/test-profile
MISTRAL_API_KEY=test-key
```

**config.json:**
```json
{
  "threads": 1,
  "scraper_timeout": 60
}
```

**Result:**
- Fast headless testing
- Verbose output for debugging
- Minimal resource usage

---

## Default Values

All default values are centralized in `src/constants.py`:

```python
# Application Settings
DEFAULT_VERBOSE = False
DEFAULT_HEADLESS = False
DEFAULT_IS_FOR_KIDS = False
DEFAULT_THREADS = 1
DEFAULT_SCRIPT_SENTENCE_LENGTH = 4
DEFAULT_TWITTER_LANGUAGE = "en"

# Network/Scraper Settings
DEFAULT_SCRAPER_TIMEOUT = 300  # 5 minutes
DEFAULT_HTTP_TIMEOUT = 5       # For health checks

# SMTP/Email Settings
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587

# See src/constants.py for complete list
```

**Benefits:**
- Single source of truth
- Easy to modify defaults
- Clear documentation
- Type safety

---

## Validation

### Automatic Validation

The application uses **Pydantic** for automatic configuration validation:

```python
from config import ConfigManager

# Validate configuration on startup
try:
    ConfigManager.validate()
    print("✓ Configuration valid!")
except ValidationError as e:
    print(f"✗ Configuration error: {e}")
```

### Validation Rules

**Enforced by `src/config_schema.py`:**

- `threads`: Must be between 1 and 32
- `script_sentence_length`: Must be between 1 and 20
- `scraper_timeout`: Must be between 30 and 3600 seconds
- `firefox_profile`: Cannot be empty string
- `font`: Must have valid extension (.ttf, .otf, .ttc, .woff, .woff2)
- `imagemagick_path`: Validated for command injection attacks

### Manual Validation

```python
from config_schema import validate_config
from config import ConfigManager

# Load and validate
config_dict = ConfigManager._config
validated = validate_config(config_dict)
```

---

## Troubleshooting

### Common Issues

#### 1. "Firefox profile not found"

**Problem:** `firefox_profile` path is invalid or doesn't exist.

**Solution:**
```bash
# Find your Firefox profile
# macOS
ls ~/Library/Application Support/Firefox/Profiles/

# Linux
ls ~/.mozilla/firefox/

# Windows
dir %APPDATA%\Mozilla\Firefox\Profiles\

# Set in .env
FIREFOX_PROFILE=/path/to/your/profile
```

#### 2. "API key not working"

**Problem:** API keys not being read correctly.

**Solution:**
```bash
# Check .env file exists and has correct format
cat .env | grep API_KEY

# Verify no trailing spaces
MISTRAL_API_KEY=sk-abc123   # GOOD
MISTRAL_API_KEY=sk-abc123   # BAD (trailing space)

# Check environment variable is set
echo $MISTRAL_API_KEY
```

#### 3. "Configuration validation failed"

**Problem:** Invalid values in config.json.

**Solution:**
```python
# Run validation to see specific errors
from config import ConfigManager
try:
    ConfigManager.validate()
except Exception as e:
    print(f"Validation errors:\n{e}")
```

#### 4. "Value not updating"

**Problem:** Changed config.json but value doesn't update.

**Possible causes:**
1. Environment variable is overriding it
2. Need to restart application
3. Typo in config key

**Solution:**
```bash
# Check environment variables
env | grep -i verbose

# Unset if needed
unset VERBOSE

# Verify config.json syntax
python -m json.tool config.json
```

---

## Best Practices

### ✅ Do

- **Use environment variables for secrets** (API keys, passwords)
- **Use config.json for non-sensitive settings** (threads, timeouts)
- **Keep .env file in .gitignore** (already done)
- **Provide .env.example** for documentation
- **Validate configuration on startup**
- **Use descriptive variable names**

### ❌ Don't

- **Don't commit secrets to git** (use .env instead)
- **Don't hard-code configuration** (use constants.py)
- **Don't mix config sources** (pick env var OR config.json per setting)
- **Don't use production keys in development**
- **Don't skip validation** (catch errors early)

---

## Configuration Checklist

Before running the application:

- [ ] Created `.env` file from `.env.example`
- [ ] Set all required API keys in `.env`
- [ ] Configured `firefox_profile` path (env var or config.json)
- [ ] Verified `config.json` has valid JSON syntax
- [ ] Set application settings (verbose, headless, threads, etc.)
- [ ] Ran configuration validation (`ConfigManager.validate()`)
- [ ] Checked `.env` is in `.gitignore`
- [ ] Documented any custom settings for your team

---

## See Also

- **[SECRETS_MANAGEMENT.md](../SECRETS_MANAGEMENT.md)** - Detailed guide on API key management
- **[DEPENDENCY_MANAGEMENT.md](../DEPENDENCY_MANAGEMENT.md)** - Managing project dependencies
- **[src/constants.py](../src/constants.py)** - All default values
- **[src/config_schema.py](../src/config_schema.py)** - Validation schema
- **[src/config.py](../src/config.py)** - Configuration manager implementation

---

**Last Updated:** 2025-11-06
**Version:** 1.0
