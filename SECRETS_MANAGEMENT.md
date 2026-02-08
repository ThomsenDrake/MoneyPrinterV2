# Secrets Management Guide

**Last Updated:** 2025-11-06
**Status:** Implemented in Phase 5

---

## Overview

AutoMuse now supports **environment variable-based secrets management** with automatic fallback to `config.json` for backward compatibility. This approach follows security best practices and prevents accidental exposure of API keys and credentials.

## Priority Order

The application checks for configuration values in this order:

1. **Environment Variables** (highest priority) - Checked first
2. **config.json** (fallback) - Used if environment variable not set
3. **Default Values** (last resort) - Used if neither above exist

## Supported Environment Variables

### Critical Secrets

| Environment Variable | Purpose | Required |
|---------------------|---------|----------|
| `ASSEMBLYAI_API_KEY` | AssemblyAI API for subtitle generation | Optional* |
| `MISTRAL_API_KEY` | Mistral AI API for text generation | **Yes** |
| `VENICE_API_KEY` | Venice AI API for image generation | Optional* |
| `SMTP_USERNAME` | Email address for outreach | Optional* |
| `SMTP_PASSWORD` | Email password/app password | Optional* |

*Required only if using the corresponding feature.

### Configuration Variables

| Environment Variable | Purpose | Default |
|---------------------|---------|---------|
| `VERBOSE` | Enable verbose logging | `false` |
| `FIREFOX_PROFILE` | Path to Firefox profile | `""` (empty) |
| `HEADLESS` | Run browser in headless mode | `false` |
| `SMTP_SERVER` | SMTP server for email | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |

For a complete list of environment variables, see `.env.example`.

## Setup Instructions

### Method 1: Using .env File (Recommended)

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env and add your secrets:**
   ```bash
   # Edit with your favorite editor
   nano .env
   # or
   vim .env
   ```

3. **Fill in your API keys:**
   ```bash
   MISTRAL_API_KEY=your_actual_mistral_api_key_here
   VENICE_API_KEY=your_actual_venice_api_key_here
   ASSEMBLYAI_API_KEY=your_actual_assemblyai_key_here

   # For email outreach (optional)
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password_here
   ```

4. **Verify .env is gitignored:**
   ```bash
   # Should show .env is ignored
   git check-ignore .env
   ```

### Method 2: System Environment Variables

For production/cloud environments, set environment variables directly:

```bash
# Linux/macOS
export MISTRAL_API_KEY="your_key_here"
export VENICE_API_KEY="your_key_here"

# Windows PowerShell
$env:MISTRAL_API_KEY="your_key_here"
$env:VENICE_API_KEY="your_key_here"

# Windows Command Prompt
set MISTRAL_API_KEY=your_key_here
set VENICE_API_KEY=your_key_here
```

### Method 3: Docker Environment

When using Docker, pass environment variables:

```bash
# Using docker run
docker run -e MISTRAL_API_KEY="your_key" \
           -e VENICE_API_KEY="your_key" \
           moneyprinter:latest

# Using docker-compose
# Add to docker-compose.yml:
services:
  moneyprinter:
    environment:
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
      - VENICE_API_KEY=${VENICE_API_KEY}
    env_file:
      - .env
```

## Backward Compatibility

**Important:** The application maintains full backward compatibility with `config.json`.

- If you have existing `config.json` with API keys, it will continue to work
- Environment variables take precedence over `config.json` values
- No migration required for existing installations

### Migration Path (Optional)

To migrate from `config.json` to `.env`:

1. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

2. **Copy secrets from config.json to .env:**
   ```bash
   # Extract from config.json
   MISTRAL_API_KEY=$(jq -r '.mistral_api_key' config.json)

   # Add to .env
   echo "MISTRAL_API_KEY=$MISTRAL_API_KEY" >> .env
   ```

3. **Remove secrets from config.json:**
   ```json
   {
     "mistral_api_key": "",
     "venice_api_key": "",
     "assembly_ai_api_key": "",
     "email": {
       "username": "",
       "password": ""
     }
   }
   ```

4. **Test the application:**
   ```bash
   python src/main.py
   ```

## Security Best Practices

### ✅ DO

- ✅ Use `.env` file for local development
- ✅ Use system environment variables for production
- ✅ Keep `.env` in `.gitignore` (already configured)
- ✅ Use different API keys for dev/staging/prod
- ✅ Rotate API keys periodically
- ✅ Use Google App Passwords for Gmail (not your real password)
- ✅ Set file permissions on .env: `chmod 600 .env`

### ❌ DON'T

- ❌ Commit `.env` to version control
- ❌ Share your `.env` file
- ❌ Store secrets in `config.json` (use env vars instead)
- ❌ Hardcode API keys in source code
- ❌ Post API keys in GitHub issues/discussions
- ❌ Use production keys in development

## Verifying Your Setup

Run this quick verification:

```bash
# Check if environment variables are loaded
python -c "import os; print('MISTRAL_API_KEY:', 'SET' if os.getenv('MISTRAL_API_KEY') else 'NOT SET')"

# Or run the health checks
python -c "from src.health_checks import HealthChecker; HealthChecker.validate_startup()"
```

## Troubleshooting

### Issue: "API key not found"

**Solution:**
1. Check if `.env` file exists: `ls -la .env`
2. Verify `.env` has correct key names (uppercase)
3. Ensure no trailing spaces in `.env` file
4. Check file permissions: `chmod 600 .env`

### Issue: "Environment variables not loading"

**Solution:**
1. Install python-dotenv: `pip install python-dotenv`
2. Restart your terminal/IDE
3. Verify `.env` is in project root directory
4. Check for syntax errors in `.env` (no spaces around `=`)

### Issue: "Using old config.json values"

**Explanation:** This is expected behavior. The application checks environment variables first, then falls back to `config.json`. If both are set, environment variables take precedence.

**To force env vars only:**
1. Remove secrets from `config.json`
2. Ensure environment variables are set
3. Restart the application

## Example .env File

Here's a complete example (do not commit this file!):

```bash
# AutoMuse Environment Variables
# NEVER commit this file to version control!

# =============================================================================
# CRITICAL SECRETS
# =============================================================================

ASSEMBLYAI_API_KEY=sk_1234567890abcdefghijklmnopqrstuvwxyz
MISTRAL_API_KEY=sk_abcdefghijklmnopqrstuvwxyz1234567890
VENICE_API_KEY=vapi_zyxwvutsrqponmlkjihgfedcba

# Gmail/SMTP (use App Password, not real password!)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # 16-character app password

# =============================================================================
# CONFIGURATION
# =============================================================================

VERBOSE=true
HEADLESS=false
FIREFOX_PROFILE=/home/user/.mozilla/firefox/your-profile.default
THREADS=4
```

## Code Implementation Details

### How It Works

The `ConfigManager` class in `src/config.py` includes a new method:

```python
@classmethod
def get_with_env(cls, key: str, env_var: str, default: Any = None) -> Any:
    """
    Get a configuration value with environment variable priority.

    Order of precedence:
    1. Environment variable (if set and not empty)
    2. config.json value (if key exists)
    3. Default value
    """
    # Check environment variable first
    env_value = os.getenv(env_var)
    if env_value is not None and env_value.strip() != "":
        return env_value

    # Fall back to config.json
    instance = cls()
    return instance._config.get(key, default)
```

### Updated Getter Functions

All sensitive configuration getters now use this pattern:

```python
def get_mistral_api_key() -> str:
    """Gets Mistral AI API key from MISTRAL_API_KEY env var or config.json."""
    return _config.get_with_env("mistral_api_key", "MISTRAL_API_KEY", "")
```

## CI/CD Integration

For GitHub Actions or other CI/CD systems:

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run tests
        env:
          MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
          VENICE_API_KEY: ${{ secrets.VENICE_API_KEY }}
        run: |
          pytest tests/
```

Store secrets in GitHub Settings → Secrets → Actions.

## Related Documentation

- **Environment Setup:** See `ENV_SETUP.md`
- **Cloud Deployment:** See `CLOUD_SETUP_RECOMMENDATIONS.md`
- **Dependency Management:** See `DEPENDENCY_MANAGEMENT.md`
- **Phase 5 Summary:** See `PHASE_5_SUMMARY.md` (when available)

## Support

If you encounter issues with secrets management:

1. Review this document thoroughly
2. Check `.env.example` for correct variable names
3. Verify your API keys are valid at the provider's website
4. Run health checks: `python -c "from src.health_checks import HealthChecker; HealthChecker.validate_startup()"`
5. Check logs in `logs/automuse.log` for detailed error messages

---

**Security Notice:** This document contains examples only. Never share your actual API keys or passwords. Treat them like passwords - keep them secret and secure.
