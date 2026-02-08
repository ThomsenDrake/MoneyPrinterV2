# MoneyPrinterV2 - AI Agent Guide

This document provides essential information for AI coding agents working with the MoneyPrinterV2 project. It covers the project architecture, development practices, and key technical details.

## Project Overview

MoneyPrinterV2 is an automated content creation and social media management platform that generates YouTube Shorts, manages Twitter accounts, handles affiliate marketing, and performs business outreach. It's a Python-based CLI application with a modular architecture designed for automation and scalability.

**Key Features:**
- YouTube Shorts automation (video generation, upload, scheduling)
- Twitter bot with automated posting and scheduling
- Affiliate marketing integration with Amazon
- Business outreach and cold email automation
- CRON job scheduling for all features

## Technology Stack

**Core Technologies:**
- **Language:** Python 3.9+ (strict requirement)
- **Web Automation:** Selenium WebDriver with Firefox/Geckodriver
- **Video Processing:** MoviePy with ImageMagick for subtitle rendering
- **Text-to-Speech:** CoquiTTS
- **AI Services:** 
  - Mistral AI for text generation
  - Venice AI for image generation
  - AssemblyAI for speech-to-text/subtitle generation
- **Configuration:** Pydantic for validation, environment variables + JSON config
- **Testing:** pytest with coverage reporting
- **Code Quality:** Black, isort, flake8, mypy, pre-commit hooks

**Build & Deployment:**
- **Containerization:** Docker with multi-stage builds
- **Dependency Management:** pip with requirements.txt
- **CI/CD:** GitHub Actions (pre-commit hooks configured)

## Project Architecture

### Directory Structure
```
src/                    # Main application source
├── classes/           # Core feature implementations
│   ├── YouTube.py     # YouTube automation (35K+ lines)
│   ├── Twitter.py     # Twitter bot functionality
│   ├── Tts.py         # Text-to-speech wrapper
│   ├── AFM.py         # Affiliate marketing
│   └── Outreach.py    # Business outreach
├── main.py            # CLI entry point and menu system
├── config.py          # Configuration management
├── constants.py       # All default values and constants
├── account_manager.py # Multi-account management
├── scheduler_service.py # CRON job scheduling
├── validation.py      # Input validation utilities
├── cache.py          # Local caching system
└── [other utilities]

tests/                 # Comprehensive test suite
├── test_*.py         # Unit tests for each module
└── conftest.py       # pytest configuration

docs/                  # Documentation
scripts/               # Utility scripts
fonts/                 # Subtitle fonts
assets/                # Static assets
```

### Configuration Hierarchy
The project uses a 3-tier configuration system (highest to lowest priority):
1. **Environment Variables** (`.env` file) - For secrets and deployment-specific settings
2. **config.json** - Non-sensitive configuration options
3. **constants.py** - Default fallback values

**Critical:** API keys and secrets must be in `.env`, never in config.json or code.

### Key Classes & Modules

**Core Classes:**
- `YouTube`: Handles video generation, upload, and account management
- `Twitter`: Manages Twitter posting and account automation
- `AffiliateMarketing`: Amazon affiliate integration
- `Outreach`: Business discovery and email automation
- `TTS`: Text-to-speech wrapper around CoquiTTS

**Utility Modules:**
- `AccountManager`: Multi-account management system
- `SchedulerService`: CRON job setup and management
- `HTTPClient`: Rate-limited HTTP client with retry logic
- `LLMService`: Unified interface for AI services
- `BrowserFactory`: Selenium WebDriver management
- `Cache`: Local file-based caching system

## Development Practices

### Code Style Guidelines
- **Line Length:** 100 characters maximum
- **Formatting:** Black with isort for imports
- **Type Hints:** Encouraged but not enforced (mypy configured)
- **Docstrings:** Google-style for all public functions/classes
- **Naming:** snake_case for functions/variables, PascalCase for classes

### Testing Strategy
- **Framework:** pytest with coverage reporting
- **Test Markers:** 
  - `@pytest.mark.unit` - Unit tests without external dependencies
  - `@pytest.mark.integration` - Tests requiring external services
  - `@pytest.mark.slow` - Time-consuming tests
  - `@pytest.mark.selenium` - Browser automation tests
- **Coverage Target:** Comprehensive coverage with HTML reports
- **Mocking:** pytest-mock for external dependencies

### Quality Assurance
```bash
# Run all quality checks
make quality

# Individual commands
make lint          # flake8
make format        # Black + isort
make type-check    # mypy
make test          # pytest with coverage
make clean         # Remove artifacts
```

### Pre-commit Hooks
Configured hooks include:
- Black code formatting
- isort import sorting
- flake8 linting
- mypy type checking
- General file cleanup (trailing whitespace, etc.)

## Build and Test Commands

### Local Development
```bash
# Setup
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run application
python src/main.py

# Development commands
make install       # Install dependencies
make test          # Run all tests
make test-unit     # Unit tests only
make quality       # All quality checks
make all           # Format + quality checks
```

### Docker Development
```bash
# Using pre-built image
docker-compose up

# Build from source
docker-compose --build up

# Direct Docker
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  ghcr.io/thomsendrake/moneyprinterv2:latest
```

## Configuration Requirements

### Essential Environment Variables (.env)
```bash
# Critical API Keys
ASSEMBLYAI_API_KEY=     # Speech-to-text
MISTRAL_API_KEY=        # Text generation  
VENICE_API_KEY=         # Image generation
SMTP_USERNAME=          # Email outreach
SMTP_PASSWORD=          # Gmail app password

# Basic Settings
VERBOSE=true            # Enable verbose logging
HEADLESS=false          # Browser headless mode
FIREFOX_PROFILE=        # Optional custom Firefox profile
```

### Configuration File (config.json)
```json
{
  "verbose": true,
  "headless": false,
  "twitter_language": "English",
  "threads": 2,
  "font": "bold_font.ttf",
  "imagemagick_path": "/usr/bin/convert",
  "script_sentence_length": 4
}
```

## Security Considerations

### API Key Management
- **Never commit API keys to version control**
- Use `.env` file for all secrets
- Rotate keys regularly
- Use environment-specific configurations
- Monitor API usage and rate limits

### Browser Automation Security
- Firefox profiles are isolated per account
- Headless mode available for server deployment
- User-agent rotation not implemented (consider for scale)
- Proxy support available but not configured by default

### Network Security
- Rate limiting implemented for all external APIs
- Retry logic with exponential backoff
- HTTP timeout configurations
- SSL verification enabled by default

## Deployment Notes

### System Requirements
- **Python:** 3.9+ (strict requirement for dependencies)
- **Memory:** Minimum 4GB RAM recommended
- **CPU:** Multi-core for video processing
- **Storage:** Adequate space for video generation
- **Network:** Stable internet for API calls

### External Dependencies
- **Firefox Browser:** For Selenium automation
- **Geckodriver:** WebDriver for Firefox
- **ImageMagick:** Video subtitle rendering
- **FFmpeg:** Video processing (via MoviePy)
- **Go Language:** Optional, for Google Maps scraper

### Docker Considerations
- Non-root user (mpv2user) for security
- Volume mounts for persistent data
- Resource limits configurable
- Network isolation available
- Pre-built images available on GitHub Container Registry

## Common Development Patterns

### Error Handling
- Custom exception hierarchy in `exceptions.py`
- Centralized error handling in `error_handlers.py`
- Logging with rotation and different levels
- Graceful degradation for non-critical failures

### Caching Strategy
- Local file-based caching in `cache/` directory
- JSON-based storage for structured data
- Automatic cleanup of temporary files
- Cache invalidation based on timestamps

### Multi-account Support
- UUID-based account identification
- Separate Firefox profiles per account
- Account-specific configuration storage
- Batch operations across accounts

### Rate Limiting
- Per-service rate limit configurations
- Token bucket implementation
- Automatic retry with backoff
- Service-specific limits (Mistral, Venice, AssemblyAI)

## Troubleshooting Guide

### Common Issues
1. **Firefox Profile Issues:** Check profile path and permissions
2. **ImageMagick Path:** Verify binary location for your OS
3. **API Rate Limits:** Monitor usage and adjust delays
4. **Video Processing:** Ensure adequate disk space and memory
5. **Selenium Timeouts:** Adjust wait timeouts in constants

### Debug Mode
- Enable `VERBOSE=true` in environment
- Check application logs in rotating log files
- Use browser in non-headless mode for visual debugging
- Monitor network requests via HTTP client logs

### Performance Optimization
- Adjust thread count based on CPU cores
- Use appropriate video quality settings
- Implement proxy rotation for scale
- Monitor API usage and costs

## Key Implementation Details

### Design Patterns Used
- **Singleton Pattern**: ConfigManager, HTTPClient for resource efficiency
- **Factory Pattern**: BrowserFactory for consistent browser creation
- **Service Layer**: AccountManager, SchedulerService for business logic
- **Dependency Injection**: Browser and HTTP client injection for testability
- **Context Managers**: Proper resource cleanup in Twitter class

### Security Measures
- Input validation and sanitization in validation.py
- Path traversal prevention with basename extraction
- Command injection prevention in ImageMagick path validation
- File locking for cross-platform cache consistency
- Environment variable prioritization for sensitive data

### Performance Optimizations
- Connection pooling in HTTPClient with requests.Session
- In-memory configuration caching to eliminate file I/O
- Multi-threaded image generation in YouTube class
- Lazy loading of optional dependencies

### Cross-Platform Compatibility
- Platform-specific file locking (msvcrt for Windows, fcntl for Unix)
- Path handling with pathlib for consistent behavior
- Browser profile management across operating systems

This guide should provide sufficient context for AI agents to effectively work with the MoneyPrinterV2 codebase. Always refer to the actual code and documentation for the most up-to-date information.