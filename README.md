# AutoMuse

**AutoMuse** is an AI-powered content automation platform that streamlines video generation and social media management. Originally forked from MoneyPrinterV2, AutoMuse has evolved into a robust, enterprise-grade automation system with comprehensive error handling, extensive testing, and modern software engineering practices.

> **Note:** This is a significant fork that has diverged substantially from the original MoneyPrinterV2 project, featuring enhanced architecture, security improvements, and professional tooling.

> **Requirements:** AutoMuse requires Python 3.9 or higher to function effectively.

## Features

- [x] Twitter Bot (with CRON Jobs => `scheduler`)
- [x] YouTube Shorts Automater (with CRON Jobs => `scheduler`)
- [x] Affiliate Marketing (Amazon + Twitter)
- [x] Find local businesses & cold outreach

## Origins

AutoMuse is forked from [MoneyPrinterV2](https://github.com/FujiwaraChoki/MoneyPrinterV2), which has various community versions including [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) (Chinese).

## Installation

### Option 1: Docker (Recommended)

The easiest way to run AutoMuse is using Docker with our pre-built image. No compilation needed!

```bash
# Clone the repository
git clone https://github.com/ThomsenDrake/MoneyPrinterV2.git
cd MoneyPrinterV2

# Setup configuration files
cp .env.example .env
cp config.example.json config.json
# Edit .env and config.json with your API keys and settings

# Pull and run with Docker Compose (uses pre-built image)
docker-compose up
```

**Or use docker directly:**

```bash
# Pull the image
docker pull ghcr.io/thomsendrake/automuse:latest

# Run it
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  ghcr.io/thomsendrake/automuse:latest
```

For detailed Docker instructions, building from source, and advanced configurations, see [DOCKER.md](DOCKER.md).

### Option 2: Local Installation

Please install [Microsoft Visual C++ build tools](https://visualstudio.microsoft.com/de/visual-cpp-build-tools/) first, so that CoquiTTS can function correctly.

> ⚠️ If you are planning to reach out to scraped businesses per E-Mail, please first install the [Go Programming Language](https://golang.org/).

```bash
git clone https://github.com/ThomsenDrake/MoneyPrinterV2.git

cd MoneyPrinterV2
# Copy Example Configuration and fill out values in config.json
cp config.example.json config.json

# Create a virtual environment
python -m venv venv

# Activate the virtual environment - Windows
.\venv\Scripts\activate

# Activate the virtual environment - Unix
source venv/bin/activate

# Install the requirements
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python src/main.py
```

## Documentation

All relevant document can be found [here](docs/).

## Scripts

For easier usage, there are some scripts in the `scripts` directory, that can be used to directly access the core functionality of AutoMuse, without the need of user interaction.

All scripts need to be run from the root directory of the project, e.g. `bash scripts/upload_video.sh`.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us. Check out [docs/Roadmap.md](docs/Roadmap.md) for a list of features that need to be implemented.

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

AutoMuse is licensed under `Affero General Public License v3.0`. See [LICENSE](LICENSE) for more information.

## Acknowledgments

- [CoquiTTS](https://github.com/coqui-ai/TTS)
- [Mistral AI](https://mistral.ai/) - Text generation API
- [Venice AI](https://venice.ai/) - Image generation API

## Disclaimer

This project is for educational purposes only. The author will not be responsible for any misuse of the information provided. All the information is published in good faith and for general information purpose only. The author does not make any warranties about the completeness, reliability, and accuracy of this information. Any action you take upon the information you find in this repository is strictly at your own risk. The author will not be liable for any losses and/or damages in connection with the use of this software.
