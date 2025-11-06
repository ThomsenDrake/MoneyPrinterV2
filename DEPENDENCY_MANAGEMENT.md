# Dependency Management Guide

This document explains how to manage dependencies in MoneyPrinterV2.

## Overview

The project uses **pip-tools** for dependency management, which provides:
- **Reproducible builds** - Lock files ensure everyone uses the same versions
- **Clear dependency hierarchy** - Separate direct vs. transitive dependencies
- **Easy updates** - Update all dependencies with a single command
- **Security** - Automated vulnerability scanning with Dependabot

## File Structure

```
requirements.in          # Direct production dependencies
requirements.txt         # Locked production dependencies (generated)
requirements-dev.in      # Direct development dependencies
requirements-dev.txt     # Locked development dependencies (generated)
requirements-test.txt    # Testing dependencies for CI/CD (generated)
```

### File Purposes

- **requirements.txt** - Production dependencies only. Install this in production environments.
- **requirements-dev.txt** - All development tools (testing, linting, formatting, security). Install this for local development.
- **requirements-test.txt** - Minimal set for CI/CD pipelines (production + testing + quality tools).
- **requirements.in** - Human-maintained list of direct production dependencies.
- **requirements-dev.in** - Human-maintained list of direct development dependencies.

## Setup

### Install pip-tools

```bash
pip install pip-tools
```

### Install Dependencies

**Production environment:**
```bash
pip install -r requirements.txt
```

**Local development (recommended):**
```bash
pip install -r requirements-dev.txt
```

**CI/CD pipelines:**
```bash
pip install -r requirements-test.txt
```

## Adding New Dependencies

### Production Dependency

1. Add to `requirements.in`:
   ```
   new-package>=1.2.3
   ```

2. Compile lock file:
   ```bash
   pip-compile requirements.in
   ```

3. Install:
   ```bash
   pip install -r requirements.txt
   ```

### Development Dependency

1. Add to `requirements-dev.in`:
   ```
   new-dev-tool>=2.0.0
   ```

2. Compile lock file:
   ```bash
   pip-compile requirements-dev.in
   ```

3. Install:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Updating Dependencies

### Update All Dependencies

```bash
# Update production dependencies
pip-compile requirements.in --upgrade

# Update development dependencies
pip-compile requirements-dev.in --upgrade

# Install updated dependencies
pip install -r requirements-dev.txt
```

### Update Specific Package

```bash
# Update only one package
pip-compile requirements.in --upgrade-package requests

# Install the update
pip install -r requirements.txt
```

### Update Security Patches Only

```bash
# Updates to latest patch version only (e.g., 1.2.3 -> 1.2.4)
pip-compile requirements.in --upgrade --allow-unsafe
```

## Version Pinning Strategy

We use **compatible release** specifiers for dependencies:

```python
# Good - allows minor and patch updates
requests>=2.31.0,<3.0.0

# Alternative syntax (same meaning)
requests~=2.31.0

# Avoid - too restrictive
requests==2.31.0
```

This allows:
- ✅ Patch updates (2.31.0 → 2.31.1) - bug fixes
- ✅ Minor updates (2.31.0 → 2.32.0) - new features
- ❌ Major updates (2.31.0 → 3.0.0) - breaking changes

## Automated Security Updates

The project uses **GitHub Dependabot** for automated security updates:

- **Location**: `.github/dependabot.yml`
- **Schedule**: Weekly checks
- **Scope**: Both production and development dependencies

Dependabot will:
1. Detect security vulnerabilities
2. Create pull requests with fixes
3. Run CI tests automatically
4. Notify via GitHub notifications

## Checking for Vulnerabilities

### Using Safety

```bash
# Install safety
pip install safety

# Check for known security vulnerabilities
safety check --file requirements.txt

# Check with detailed output
safety check --file requirements.txt --full-report
```

### Using pip-audit

```bash
# Install pip-audit
pip install pip-audit

# Audit installed packages
pip-audit

# Audit requirements file
pip-audit -r requirements.txt
```

## Best Practices

### 1. Keep .in Files Minimal

Only list **direct dependencies** in `.in` files:

```python
# ✅ Good - direct dependency
requests>=2.31.0

# ❌ Bad - transitive dependency (requests already includes urllib3)
urllib3>=2.0.0
```

### 2. Use Constraints

When multiple packages depend on the same library, use constraints:

```python
# requirements.in
package-a>=1.0.0
package-b>=2.0.0

# If both need compatible versions of shared-lib
shared-lib>=1.5.0,<2.0.0
```

### 3. Document Security Requirements

When pinning to a specific version for security:

```python
# Security: CVE-2023-XXXXX fixed in 10.4.0
Pillow>=10.4.0
```

### 4. Regular Updates

Update dependencies regularly:
- **Security patches**: Immediately
- **Minor updates**: Monthly
- **Major updates**: Quarterly (with thorough testing)

## Troubleshooting

### Conflict Resolution

If pip-compile reports conflicts:

1. Check the error message for conflicting packages
2. Adjust version constraints in `.in` files
3. Try upgrading the conflicting package:
   ```bash
   pip-compile requirements.in --upgrade-package problematic-package
   ```

### Dependency Tree

View why a package is installed:

```bash
pip install pipdeptree
pipdeptree -p package-name
```

### Clean Install

For a fresh environment:

```bash
# Create new virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
```

## CI/CD Integration

Our GitHub Actions workflow:

1. Installs dependencies from lock files
2. Runs tests with exact versions
3. Fails if `requirements.txt` is out of date

To update lock files in CI:

```yaml
- name: Update dependencies
  run: |
    pip install pip-tools
    pip-compile requirements.in
    pip-compile requirements-dev.in
```

## Migration from requirements.txt

If you're migrating an existing `requirements.txt`:

```bash
# Backup current file
cp requirements.txt requirements.txt.backup

# Create .in file with current dependencies
# (manually review and keep only direct dependencies)
cat requirements.txt > requirements.in

# Generate new lock file
pip-compile requirements.in

# Verify everything still works
pip install -r requirements.txt
python -m pytest
```

## Additional Resources

- [pip-tools documentation](https://pip-tools.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Dependabot documentation](https://docs.github.com/en/code-security/dependabot)
- [PEP 440 - Version Specifiers](https://peps.python.org/pep-0440/)

## Questions?

For questions about dependency management:
1. Check this guide first
2. Review the pip-tools documentation
3. Open an issue on GitHub
