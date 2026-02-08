# Docker Deployment Guide for AutoMuse

This guide explains how to deploy and run AutoMuse using Docker containers.

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 1.29 or later
- At least 4GB of RAM available for the container
- At least 10GB of free disk space

## Quick Start

### Option A: Using Pre-built Image (Fastest)

Pull and run the pre-built image from GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/thomsendrake/automuse:latest

# Setup configuration files
cp .env.example .env
cp config.example.json config.json
# Edit .env and config.json with your API keys and settings

# Run with docker-compose
docker-compose up
```

### Option B: Build from Source

If you want to build the image yourself or make custom modifications:

#### 1. Setup Configuration Files

Before running the Docker container, you need to set up your configuration files:

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env and fill in your API keys and settings

# Copy and configure application settings
cp config.example.json config.json
# Edit config.json with your preferences
```

**Important:** Make sure to fill in at least the following required API keys in `.env`:
- `MISTRAL_API_KEY` - For text generation
- `VENICE_API_KEY` - For image generation
- `ASSEMBLYAI_API_KEY` - For subtitle generation

#### 2. Build the Docker Image

```bash
# Build using docker-compose (recommended)
docker-compose build

# Or build directly with Docker
docker build -t automuse:latest .
```

#### 3. Run the Container

```bash
# Run with docker-compose (recommended)
docker-compose run --rm automuse

# Or run directly with Docker
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/songs:/app/songs \
  -v $(pwd)/fonts:/app/fonts \
  automuse:latest
```

## Using the Pre-built Image

The Docker image is automatically built and published to GitHub Container Registry on every push to the main branch.

### First-Time Setup (Repository Owner)

After merging this PR, the GitHub Actions workflow will automatically build and publish the Docker image. You'll need to make the package public so users can pull it:

1. Go to your GitHub repository
2. Click on "Packages" on the right sidebar (or visit https://github.com/users/ThomsenDrake/packages)
3. Find the `automuse` package
4. Click "Package settings"
5. Scroll to "Danger Zone"
6. Click "Change visibility" and set to "Public"
7. Connect the package to your repository for better visibility

Once the package is public, anyone can pull it with `docker pull ghcr.io/thomsendrake/automuse:latest`

### Available Tags

- `latest` - Latest stable build from main branch (linux/amd64)
- `v*.*.*` - Specific version releases (e.g., `v2.0.0`)
- `main` - Latest commit on main branch

**Note:** Images are currently built for `linux/amd64` only for faster build times. ARM64 support (for M1/M2 Macs) can be added if there's demand. ARM Mac users can still run the amd64 images using Docker's emulation, though performance may be slightly reduced.

### Pull Commands

```bash
# Latest stable version
docker pull ghcr.io/thomsendrake/automuse:latest

# Specific version
docker pull ghcr.io/thomsendrake/automuse:v2.0.0

# Latest main branch
docker pull ghcr.io/thomsendrake/automuse:main
```

### Run Pre-built Image

```bash
# Quick run (interactive mode)
docker run -it --rm \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/songs:/app/songs \
  -v $(pwd)/fonts:/app/fonts \
  ghcr.io/thomsendrake/automuse:latest
```

## Docker Compose Configuration

The `docker-compose.yml` file is pre-configured with sensible defaults:

- **Interactive Mode:** `stdin_open` and `tty` are enabled for CLI interaction
- **Environment Variables:** Loaded from `.env` file
- **Persistent Volumes:** Mounted for cache, output, songs, and fonts
- **Resource Limits:** Set to 4GB RAM and 4 CPU cores (adjustable)

### Customizing docker-compose.yml

You can modify the `docker-compose.yml` file to suit your needs:

```yaml
# Adjust resource limits
deploy:
  resources:
    limits:
      cpus: '8'      # Increase CPU cores
      memory: 8G     # Increase memory
```

## Volume Mounts Explained

The following directories are mounted as volumes for data persistence:

| Host Directory | Container Path | Purpose |
|---------------|----------------|---------|
| `./cache` | `/app/cache` | Stores account data and cache |
| `./output` | `/app/output` | Generated videos and content |
| `./songs` | `/app/songs` | Background music files |
| `./fonts` | `/app/fonts` | Fonts for video subtitles |
| `./temp` | `/app/temp` | Temporary processing files |
| `./config.json` | `/app/config.json` | Application configuration (read-only) |
| `./.env` | `/app/.env` | Environment variables (read-only) |

## Running in Detached Mode

For long-running scheduled tasks:

```bash
# Start container in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down
```

## Browser Automation Considerations

AutoMuse uses Selenium with Firefox for browser automation. In Docker:

- **Headless Mode:** Set `HEADLESS=true` in `.env` for server environments
- **Firefox Profile:** Custom profiles can be mounted if needed
- **Display Issues:** If you need to see the browser, consider using X11 forwarding or VNC

### Using X11 for GUI Display (Linux/macOS)

If you need to see the Firefox browser in non-headless mode:

```bash
# Allow X11 connections
xhost +local:docker

# Run with display
docker run -it --rm \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  --env-file .env \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/cache:/app/cache \
  -v $(pwd)/output:/app/output \
  automuse:latest
```

## Troubleshooting

### Permission Issues

If you encounter permission issues with mounted volumes:

```bash
# Fix permissions on host
sudo chown -R 1000:1000 cache output songs fonts temp

# Or run container as root (not recommended for production)
docker-compose run --user root automuse
```

### Memory Issues

If the container runs out of memory:

1. Increase Docker's memory limit in Docker Desktop settings
2. Adjust `THREADS` in `.env` to use fewer CPU threads
3. Increase memory limits in `docker-compose.yml`

### Build Failures

If the build fails:

```bash
# Clean Docker cache and rebuild
docker-compose build --no-cache

# Check Docker logs
docker-compose logs
```

### ImageMagick Policy Errors

If you get ImageMagick policy errors, the Dockerfile includes a fix. If issues persist:

```bash
# Check ImageMagick policy in container
docker-compose run --rm automuse cat /etc/ImageMagick-6/policy.xml
```

## Environment Variables

Key environment variables you should configure in `.env`:

```bash
# Required API Keys
MISTRAL_API_KEY=your_mistral_key_here
VENICE_API_KEY=your_venice_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_key_here

# Docker-optimized settings
HEADLESS=true                    # Run browser in headless mode
VERBOSE=true                     # Enable detailed logging
THREADS=2                        # CPU threads for video processing
IMAGEMAGICK_PATH=/usr/bin/convert  # Already set in Dockerfile

# Browser configuration
FIREFOX_PROFILE=                 # Leave empty for default
```

## Security Best Practices

1. **Never commit secrets:** Keep `.env` and `config.json` out of version control
2. **Use read-only mounts:** Config files are mounted as read-only (`:ro`)
3. **Run as non-root:** Container uses `automuseuser` (UID 1000) by default
4. **Limit resources:** Resource limits prevent container from consuming all system resources
5. **Network isolation:** Container uses a dedicated bridge network

## Production Deployment

For production deployments:

1. **Use environment-specific configs:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

2. **Enable automatic restarts:**
   ```yaml
   restart: always
   ```

3. **Set up monitoring:**
   ```bash
   # Monitor container health
   docker stats automuse

   # View logs
   docker logs -f automuse
   ```

4. **Use Docker secrets for sensitive data:**
   ```yaml
   secrets:
     - mistral_api_key
     - venice_api_key
   ```

## Cloud Deployment

The Docker setup is ready for cloud platforms:

- **AWS ECS:** Use the Dockerfile with ECS task definitions
- **Google Cloud Run:** May need adjustments for ephemeral storage
- **Azure Container Instances:** Works with minor networking adjustments
- **DigitalOcean App Platform:** Supported with proper volume configuration
- **Kubernetes:** Can be adapted with Helm charts

See `CLOUD_SETUP_RECOMMENDATIONS.md` for cloud-specific guidance.

## Updating the Container

To update to a new version:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Cleanup

To remove all Docker artifacts:

```bash
# Stop and remove containers
docker-compose down

# Remove image
docker rmi automuse:latest

# Clean up volumes (WARNING: This deletes all data!)
docker-compose down -v
```

## Support

For Docker-specific issues:
1. Check container logs: `docker-compose logs`
2. Inspect container: `docker-compose exec automuse bash`
3. Review Docker documentation: https://docs.docker.com/

For application issues, refer to the main [README.md](README.md) and project documentation.
