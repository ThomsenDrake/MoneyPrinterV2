# AutoMuse Dockerfile
# Base image with Python 3.9
FROM python:3.9-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    # Set ImageMagick path for Linux
    IMAGEMAGICK_PATH=/usr/bin/convert

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools for Python packages
    gcc \
    g++ \
    make \
    # Firefox and geckodriver for Selenium
    firefox-esr \
    wget \
    # ImageMagick for video subtitle rendering
    imagemagick \
    # FFmpeg for video processing (required by moviepy)
    ffmpeg \
    # Audio libraries for CoquiTTS
    libsndfile1 \
    libsndfile1-dev \
    # Additional dependencies
    git \
    curl \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver for Firefox automation (pinned version for faster builds)
RUN GECKODRIVER_VERSION=v0.35.0 && \
    wget -q https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    tar -xzf geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz -C /usr/local/bin && \
    chmod +x /usr/local/bin/geckodriver && \
    rm geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz

# Configure ImageMagick to allow PDF/video operations
RUN sed -i 's/<policy domain="path" rights="none" pattern="@\*"\/>/<!-- <policy domain="path" rights="none" pattern="@*"\/> -->/g' /etc/ImageMagick-6/policy.xml

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
# Install in a single layer with proper caching for faster builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip wheel setuptools && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories for the application
RUN mkdir -p \
    cache \
    songs \
    fonts \
    temp \
    output

# Set proper permissions
RUN chmod +x src/main.py

# Create a non-root user for security
RUN useradd -m -u 1000 mpv2user && \
    chown -R mpv2user:mpv2user /app

# Switch to non-root user
USER mpv2user

# Expose any ports if needed (currently none for CLI app)
# EXPOSE 8000

# Default command
CMD ["python", "src/main.py"]
