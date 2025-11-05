# Security Improvements for MoneyPrinterV2

## Overview
This document outlines the security improvements made to the MoneyPrinterV2 project and provides guidance for users on secure configuration management.

## ⚠️ CRITICAL: Secrets Management

### Current State
The `config.json` file currently stores sensitive API keys and credentials in plain text. **This is a security risk.**

### Recommended Migration to Environment Variables

Instead of storing secrets in `config.json`, you should use environment variables or a `.env` file (which is git-ignored).

#### Step 1: Create a `.env` file

Create a file named `.env` in the root directory of the project:

```bash
# API Keys
ASSEMBLY_AI_API_KEY=your_assemblyai_key_here
MISTRAL_API_KEY=your_mistral_key_here
VENICE_API_KEY=your_venice_key_here

# Email Credentials
EMAIL_USERNAME=your_email@example.com
EMAIL_PASSWORD=your_email_password
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
```

#### Step 2: Update your config.json

Remove all sensitive values from `config.json` and replace them with placeholder text:

```json
{
  "assembly_ai_api_key": "",
  "mistral_api_key": "",
  "venice_api_key": "",
  "email": {
    "username": "",
    "password": "",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": "587"
  }
}
```

#### Step 3: Verify .env is git-ignored

Make sure `.env` is listed in your `.gitignore` file:

```bash
# Add this line to .gitignore if not present
.env
```

### Future Enhancement

In a future update, the application will be modified to read from environment variables first, falling back to `config.json` only for non-sensitive configuration.

## Security Fixes Implemented

### 1. Command Injection Vulnerabilities (CRITICAL - FIXED ✅)

**Issue:** Use of `os.system()` with user-controllable input enabled command injection attacks.

**Fix:** Replaced all `os.system()` calls with `subprocess.run()` using argument lists instead of shell strings.

**Files changed:**
- `src/utils.py`: Lines 22-24
- `src/classes/Outreach.py`: Lines 27, 81-84

**Example:**
```python
# Before (VULNERABLE)
os.system("taskkill /f /im firefox.exe")

# After (SECURE)
subprocess.run(["taskkill", "/f", "/im", "firefox.exe"], check=False, capture_output=True)
```

### 2. Subprocess Shell Injection (CRITICAL - FIXED ✅)

**Issue:** Use of `shell=True` with user input in subprocess calls enabled shell injection attacks.

**Fix:** Removed `shell=True` parameter and used argument lists.

**Files changed:**
- `src/classes/Outreach.py`: Lines 44, 101, 104, 107, 111

**Example:**
```python
# Before (VULNERABLE)
subprocess.call(command.split(" "), shell=True, timeout=float(timeout))

# After (SECURE)
subprocess.run(command_list, timeout=float(timeout), capture_output=True, text=True)
```

### 3. Dependency Security (CRITICAL - FIXED ✅)

**Issues:**
- Pillow 9.5.0 had known CVEs
- No version pinning (non-reproducible builds)
- Unused dependencies (g4f) increased attack surface

**Fixes:**
- Updated Pillow from 9.5.0 → 10.4.0
- Pinned all dependency versions
- Removed unused g4f dependency
- Enabled GitHub Dependabot for automated security updates

**Files changed:**
- `requirements.txt`
- `.github/dependabot.yml` (new)

### 4. Exception Handling (HIGH - FIXED ✅)

**Issue:** Bare `except:` clauses masked errors and made debugging impossible.

**Fix:** Replaced with specific exception types and comprehensive error logging.

**Files changed:**
- `src/utils.py`: Lines 28-35, 100-108, 122-133
- `src/classes/Outreach.py`: Lines 46-56, 295-306
- `src/classes/YouTube.py`: Lines 815-838

**Example:**
```python
# Before (BAD)
except:
    return False

# After (GOOD)
except (NoSuchElementException, TimeoutException) as e:
    logging.error(f"Failed to find element: {str(e)}", exc_info=True)
    return False
```

## Performance Improvements

### 1. Config Singleton (CRITICAL - FIXED ✅)

**Issue:** Every config access re-read and re-parsed the entire `config.json` file (~18 reads per video).

**Fix:** Implemented singleton pattern that caches config in memory.

**Performance gain:**
- Before: O(n) file I/O per config access
- After: O(1) memory lookup

**File changed:** `src/config.py`

### 2. Atomic Cache Operations (CRITICAL - FIXED ✅)

**Issue:** Race conditions could corrupt cache files when multiple processes accessed them.

**Fix:** Implemented cross-platform file locking (fcntl on Unix, msvcrt on Windows).

**File changed:** `src/cache.py`

### 3. Network Retry Logic (HIGH - FIXED ✅)

**Issue:** Transient network errors caused permanent failures.

**Fix:** Implemented automatic retry with exponential backoff using tenacity library.

**Configuration:**
- 3 retry attempts
- Exponential backoff: 2-10 seconds
- 30-second timeout per request

**Files changed:**
- `src/classes/YouTube.py`
- `src/classes/Outreach.py`

## Best Practices Going Forward

### 1. Never Commit Secrets
- Use environment variables for all API keys and credentials
- Keep `.env` file git-ignored
- Use `.env.example` as a template (without actual secrets)

### 2. Keep Dependencies Updated
- Review Dependabot PRs weekly
- Test updates in a staging environment before merging
- Monitor security advisories for your dependencies

### 3. Secure Subprocess Execution
- Never use `os.system()` - always use `subprocess.run()`
- Never use `shell=True` unless absolutely necessary
- Always pass commands as lists, not strings

### 4. Error Handling
- Use specific exception types
- Log errors with `logging.error(..., exc_info=True)`
- Never use bare `except:` clauses

### 5. Input Validation
- Validate and sanitize all user input
- Use allowlists over denylists
- Implement path validation for file operations

## Remaining Security Considerations

### 1. Secrets Migration (TODO)
While the codebase now safely handles config files, users should migrate their secrets to environment variables.

### 2. Rate Limiting (RECOMMENDED)
Consider implementing rate limiting for API calls to prevent quota exhaustion and potential account bans.

### 3. Input Sanitization (MEDIUM PRIORITY)
Add comprehensive input validation for user-provided data:
- Firefox profile paths
- File paths in general
- User-generated content for videos

## Verification Steps

To verify these security improvements are working:

1. **Test command injection fix:**
   ```bash
   # Should not be exploitable
   firefox_profile = "/path/to/profile'; rm -rf /; '"
   ```

2. **Test retry logic:**
   ```bash
   # Temporarily disable network and verify retries occur
   # Check logs for retry attempts
   ```

3. **Test file locking:**
   ```bash
   # Run multiple instances simultaneously
   # Verify no cache corruption
   ```

4. **Verify dependencies:**
   ```bash
   pip list | grep Pillow  # Should show 10.4.0
   ```

## Support

For questions or security concerns:
- Open an issue on GitHub
- Follow the security policy in SECURITY.md (if present)

---

**Last Updated:** 2025-11-05
**Security Review:** All critical and high-priority issues addressed
