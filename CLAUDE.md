# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MoneyPrinterV2 (MPV2) is a Python-based automation system for creating and managing social media content across multiple platforms. It automates video generation for YouTube Shorts, Twitter posting, affiliate marketing, and local business outreach. The project uses browser automation (Selenium), AI services (Mistral AI, Venice AI), and text-to-speech (CoquiTTS) for content generation.

**Python Version**: 3.9+ required

## Development Commands

### Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Unix
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
cp config.example.json config.json
# Edit .env and config.json with your API keys and settings
```

### Running the Application
```bash
python src/main.py
```

### Testing
```bash
make test              # Run all tests with coverage
make test-unit         # Run only unit tests (marked with @pytest.mark.unit)
pytest tests/          # Direct pytest invocation
pytest tests/test_config.py  # Run specific test file
pytest tests/ -k "test_name"  # Run tests matching pattern
pytest tests/ -m integration  # Run integration tests only
```

Test markers available: `unit`, `integration`, `slow`, `selenium`

### Code Quality
```bash
make lint              # Run flake8 linter
make format            # Format code with Black and sort imports with isort
make format-check      # Check formatting without modifying
make type-check        # Run mypy type checker
make quality           # Run all checks (lint + type-check + test)
make all               # Format code and run all quality checks
make clean             # Remove build artifacts and cache
```

### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
# Now hooks run automatically on git commit
```

### Docker
```bash
# Pull and run pre-built image
docker-compose up

# Or use docker directly
docker pull ghcr.io/thomsendrake/moneyprinterv2:latest
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  ghcr.io/thomsendrake/moneyprinterv2:latest
```

See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

## Architecture

### Core Components

**Main Entry Point**: `src/main.py` - Interactive CLI menu for all operations

**Platform Classes** (`src/classes/`):
- `YouTube.py` - Video generation, upload, scheduling for YouTube Shorts
- `Twitter.py` - Tweet generation and posting
- `AFM.py` - Affiliate marketing automation (Amazon + Twitter)
- `Outreach.py` - Local business scraping and email outreach
- `Tts.py` - Text-to-speech synthesis using CoquiTTS

**Core Services** (`src/`):
- `config.py` - ConfigManager singleton for config.json and .env
- `selenium_service.py` - SeleniumService abstraction for browser automation
- `cron.py` - Scheduler entry point for automated posting (called by system scheduler)
- `logger.py` - Centralized logging setup
- `http_client.py` - HTTP client with retry logic
- `rate_limiter.py` - Rate limiting for API calls
- `exceptions.py` - Custom exception hierarchy
- `validation.py` - Input validation utilities
- `protocols.py` - Type protocols for duck typing

**Configuration**:
- `.env` - Secrets (API keys, credentials) - **NEVER commit this file**
- `config.json` - Non-sensitive configuration (threads, timeouts, etc.)
- `config_schema.py` - Pydantic validation for config.json
- `constants.py` - Default values and constants

**Account Management**:
- `cache.py` / `account_manager.py` - Multi-account support for Twitter/YouTube
- Each platform can manage multiple accounts with different Firefox profiles

### Design Patterns

1. **Singleton Pattern**: ConfigManager caches config in memory to avoid repeated file I/O
2. **Service Layer**: SeleniumService abstracts Selenium operations with consistent error handling
3. **Exception Hierarchy**: Custom exceptions inherit from base classes (APIError, ValidationError, etc.)
4. **Protocol-Based Types**: Uses Python protocols (PEP 544) for duck typing without rigid inheritance
5. **Dependency Injection**: Platform classes receive dependencies through constructors

### Browser Automation

MoneyPrinterV2 uses Selenium with Firefox or undetected-chromedriver. Key patterns:
- SeleniumService provides high-level operations (wait_for_element, click, type_text)
- Browser instances are created per-account using Firefox profiles
- Headless mode supported via HEADLESS environment variable
- Selenium operations include automatic retries and graceful error handling

### Scheduling & CRON

The `src/cron.py` script is designed to be called by system schedulers (cron/Task Scheduler):
```bash
python src/cron.py twitter <account_uuid>
python src/cron.py youtube <account_uuid>
```

This enables automated posting at scheduled intervals without running main.py interactively.

## Configuration Management

**Secrets in .env**:
- API keys: `ASSEMBLYAI_API_KEY`, `MISTRAL_API_KEY`, `VENICE_API_KEY`
- SMTP credentials: `SMTP_USERNAME`, `SMTP_PASSWORD`
- Never commit .env to version control

**Settings in config.json**:
- Non-sensitive options (threads, timeouts, fonts, etc.)
- Can be committed to git
- Validated using Pydantic schemas in config_schema.py

**Access Configuration**:
```python
from config import get_config, get_api_key

config = get_config()  # Returns cached config dict
api_key = get_api_key("MISTRAL_API_KEY")  # Gets from env
```

## External Dependencies

**AI Services**:
- Mistral AI - Text generation (scripts, prompts)
- Venice AI - Image generation
- AssemblyAI - Speech-to-text for subtitles
- CoquiTTS - Local text-to-speech synthesis

**Browser Automation**:
- Selenium + undetected-chromedriver - Evade bot detection
- webdriver_manager - Automatic driver downloads

**Media Processing**:
- MoviePy - Video editing and composition
- Pillow - Image manipulation
- ImageMagick - Subtitle rendering (external binary)

## Testing Strategy

**Test Organization**:
- All tests in `tests/` directory
- Test discovery: `test_*.py` files with `test_*` functions
- pytest.ini and pyproject.toml configure test behavior

**Test Markers**:
```python
@pytest.mark.unit         # Fast, no external dependencies
@pytest.mark.integration  # Requires external services
@pytest.mark.slow         # Takes significant time
@pytest.mark.selenium     # Requires browser automation
```

**Coverage**:
- Target: src/ directory
- Reports: HTML (htmlcov/), terminal, XML
- Exclude: tests, venv, external libraries

**Running Specific Tests**:
```bash
pytest tests/test_config.py::test_config_manager_singleton
pytest -k "config" --verbose
pytest -m "not selenium"  # Skip browser tests
```

## Code Style

**Formatting**:
- Black formatter with 100 character line length
- isort for import sorting (Black-compatible profile)
- Enforced via pre-commit hooks and `make format`

**Linting**:
- flake8 with .flake8 config
- Max line length: 100
- Ignores: E203, W503 (Black compatibility)

**Type Checking**:
- mypy with lenient settings (check_untyped_defs=true)
- ignore_missing_imports=true for third-party libraries
- Gradually being adopted, not all code is fully typed

**Standards**:
- Python 3.9+ syntax and features
- Docstrings for public APIs
- Logging instead of print statements (except interactive UI)

## Common Development Workflows

### Adding a New Platform Integration

1. Create `src/classes/NewPlatform.py`
2. Implement required methods (similar to Twitter/YouTube pattern)
3. Add class to `src/classes/__init__.py` `__all__` list
4. Import in `src/main.py` and add menu options
5. Create unit tests in `tests/test_new_platform.py`
6. Update this CLAUDE.md if architectural changes needed

### Adding Configuration Options

1. Add to `.env.example` if secret, or `config.example.json` if non-sensitive
2. Add to `src/config_schema.py` Pydantic model for validation
3. Add default value to `src/constants.py` if applicable
4. Access via ConfigManager in code
5. Document in ENV_SETUP.md or relevant docs

### Working with Browser Automation

1. Use SeleniumService instead of raw Selenium calls
2. Use wait_for_element() instead of implicit waits
3. Handle exceptions: ElementNotFoundError, TimeoutError, BrowserOperationError
4. Log operations for debugging
5. Clean up browser instances in finally blocks

### Debugging Issues

**Enable Verbose Logging**:
```bash
export VERBOSE=true  # or set in .env
```

**Check Logs**:
- Application logs printed to console
- Use logger from `logger.py` module
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Common Issues**:
- Browser automation failures: Check Firefox profile paths, headless mode settings
- API errors: Verify API keys in .env
- Config errors: Validate against config_schema.py
- Import errors: Ensure venv is activated and dependencies installed

## Contributing

Pull requests should be opened against the `main` branch. See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines:
- One feature/bugfix per PR
- Link to an issue (create one if needed)
- Use WIP label for work-in-progress PRs
- Clear title and description

**Before Submitting PR**:
```bash
make all  # Format code and run all quality checks
```

## Additional Documentation

- [DOCKER.md](DOCKER.md) - Docker setup and deployment
- [ENV_SETUP.md](ENV_SETUP.md) - Environment configuration guide
- [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) - Managing API keys securely
- [DEPENDENCY_MANAGEMENT.md](DEPENDENCY_MANAGEMENT.md) - Dependency updates
- [CLOUD_SETUP_RECOMMENDATIONS.md](CLOUD_SETUP_RECOMMENDATIONS.md) - Cloud deployment
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md) - Known technical debt items
- [docs/Roadmap.md](docs/Roadmap.md) - Feature roadmap

## Project Context

This is a fork that has diverged significantly from the original MoneyPrinterV2 project. Major improvements include:
- Comprehensive error handling and custom exceptions
- Pydantic-based configuration validation
- Selenium service abstraction layer
- Extensive test coverage with pytest
- Pre-commit hooks and quality tooling
- Docker support with pre-built images
- Enhanced security (secrets management, .env separation)
