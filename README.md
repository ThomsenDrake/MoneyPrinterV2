# AutoMuse

[![made with python](https://img.shields.io/badge/made%20with-Python-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg?style=for-the-badge)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg?style=for-the-badge)](https://www.python.org/downloads/release/python-390/)

**AI-Powered Content Automation & Social Media Management Platform**

AutoMuse is a comprehensive automation platform that generates engaging content, manages multiple social media accounts, handles affiliate marketing, and automates business outreach. Originally forked from MoneyPrinterV2, AutoMuse has evolved into a robust, enterprise-grade automation system with comprehensive error handling, extensive testing, and modern software engineering practices.

> **Note:** This is a significant fork that has diverged substantially from the original MoneyPrinterV2 project, featuring enhanced architecture, security improvements, and professional tooling.

## 🚀 Key Features

### Content Creation
- **YouTube Shorts Automation**: Generate, edit, and upload engaging short-form videos with AI-powered scripts, voiceovers, and subtitles
- **Twitter Content Management**: Create and schedule tweets with AI-generated content and trending hashtag optimization
- **Text-to-Speech**: High-quality voice generation using CoquiTTS with multiple voice options
- **Image Generation**: AI-powered visual content creation using Venice AI

### Marketing & Outreach
- **Affiliate Marketing**: Automated Amazon affiliate product promotion with content optimization
- **Business Discovery**: Find and analyze local businesses for outreach opportunities
- **Cold Email Automation**: Personalized business outreach with scheduling and tracking
- **Multi-Platform Integration**: Seamless content distribution across platforms

### Enterprise Features
- **Multi-Account Management**: Handle multiple accounts across platforms with isolated profiles
- **CRON Job Scheduling**: Automated scheduling for all features with flexible timing
- **Rate Limit Management**: Intelligent API rate limiting with retry logic
- **Comprehensive Logging**: Detailed activity logs with rotation and analysis

## 🛠 Technology Stack

- **Core**: Python 3.9+ with modular architecture
- **Web Automation**: Selenium WebDriver with Firefox/Geckodriver
- **Video Processing**: MoviePy with ImageMagick for professional subtitle rendering
- **AI Services**: Mistral AI (text), Venice AI (images), AssemblyAI (speech-to-text)
- **Configuration**: Pydantic validation with environment variables and JSON config
- **Testing**: pytest with comprehensive coverage reporting
- **Deployment**: Docker with multi-stage builds and GitHub Container Registry

## 📦 Quick Start

### Docker Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/ThomsenDrake/MoneyPrinterV2.git
cd MoneyPrinterV2

# Setup configuration
cp .env.example .env
cp config.example.json config.json
# Edit .env with your API keys and config.json with your preferences

# Run with Docker Compose
docker-compose up
```

### Local Installation

```bash
# Clone and setup
git clone https://github.com/thomsendrake/MoneyPrinterV2.git
cd MoneyPrinterV2

# Copy and configure
cp .env.example .env
cp config.example.json config.json
# Edit configuration files with your settings

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

**System Requirements:**
- Python 3.9+ (strict requirement)
- Firefox browser
- Geckodriver for Selenium
- ImageMagick for video processing
- 4GB+ RAM recommended

## 🔧 Configuration

AutoMuse uses a 3-tier configuration system:

1. **Environment Variables** (`.env`) - API keys and sensitive data
2. **JSON Configuration** (`config.json`) - Application settings
3. **Constants** (`constants.py`) - Default fallback values

### Essential API Keys

```bash
# Required for core functionality
ASSEMBLYAI_API_KEY=     # Speech-to-text and subtitle generation
MISTRAL_API_KEY=        # AI text generation
VENICE_API_KEY=         # AI image generation

# For email outreach features
SMTP_USERNAME=          # Email account
SMTP_PASSWORD=          # App password

# Optional optimizations
FIREFOX_PROFILE=        # Custom browser profile
PROXY_SERVER=          # Proxy configuration
```

### Configuration Options

```json
{
  "verbose": true,
  "headless": false,
  "threads": 2,
  "font": "bold_font.ttf",
  "imagemagick_path": "/usr/bin/convert",
  "script_sentence_length": 4,
  "twitter_language": "English"
}
```

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Setup Guide](ENV_SETUP.md)** - Detailed installation and configuration
- **[Docker Guide](DOCKER.md)** - Container deployment options
- **[Cloud Recommendations](CLOUD_SETUP_RECOMMENDATIONS.md)** - Cloud hosting best practices
- **[Dependency Management](DEPENDENCY_MANAGEMENT.md)** - Handling dependencies
- **[Secrets Management](SECRETS_MANAGEMENT.md)** - Secure API key handling
- **[Technical Debt](TECHNICAL_DEBT.md)** - Known issues and roadmap
- **[Roadmap](docs/Roadmap.md)** - Feature roadmap and planned improvements

## 🧪 Development

### Code Quality

```bash
# Run all quality checks
make quality

# Individual commands
make lint          # Code linting with flake8
make format        # Code formatting with Black
make type-check    # Type checking with mypy
make test          # Run test suite with coverage
```

### Testing

```bash
# Run all tests
make test

# Specific test categories
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-slow         # Time-consuming tests
```

### Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for:
- Code style guidelines
- Development setup
- Pull request process
- Issue reporting

## 🐳 Docker Deployment

### Using Pre-built Images

```bash
# Pull the latest image
docker pull ghcr.io/thomsendrake/automuse:latest

# Run with docker
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  ghcr.io/thomsendrake/automuse:latest
```

### Building from Source

```bash
# Build and run with docker-compose
docker-compose build
docker-compose up

# Or build directly
docker build -t automuse .
docker run -it --rm --env-file .env automuse
```

## 🔒 Security

- **API Key Protection**: All secrets stored in environment variables
- **Browser Isolation**: Separate Firefox profiles per account
- **Input Validation**: Comprehensive sanitization and validation
- **Rate Limiting**: Built-in protection against API abuse
- **File Safety**: Path traversal prevention and secure file handling

## 📄 License

This project is licensed under the **GNU Affero General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

## ⚖️ Disclaimer

This software is provided for educational and legitimate business purposes only. Users are responsible for complying with platform terms of service and applicable laws. The developers assume no responsibility for misuse or any consequences resulting from the use of this software.

---

## 🙏 Original Project

AutoMuse is a fork of [MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2) from FujiwaraChoki. It maintains the core automation philosophy while introducing significant enhancements including comprehensive error handling, Pydantic-based configuration validation, extensive test coverage, and modern software engineering practices. We acknowledge and appreciate the original creator's innovative work and community contributions.
