# API Documentation

This directory contains the Sphinx-based API documentation for MoneyPrinterV2.

## Building the Documentation

### Prerequisites

Install documentation dependencies:

```bash
pip install -r requirements-docs.txt
```

### Build HTML Documentation

```bash
cd docs/api
make html
```

The generated HTML will be in `docs/api/_build/html/`. Open `index.html` in a browser to view.

### Build Other Formats

```bash
# PDF (requires LaTeX)
make latexpdf

# Single-page HTML
make singlehtml

# ePub
make epub
```

### Clean Build Artifacts

```bash
make clean
```

## Live Preview

For development, you can use `sphinx-autobuild` for live reloading:

```bash
sphinx-autobuild . _build/html
```

Then open http://127.0.0.1:8000 in your browser. Changes to `.rst` files will automatically rebuild and refresh.

## Documentation Structure

```
docs/api/
├── conf.py              # Sphinx configuration
├── index.rst            # Main documentation page
├── modules/             # Module-specific documentation
│   ├── core.rst        # Core modules (config, constants, etc.)
│   ├── services.rst    # Service modules (LLM, Selenium, etc.)
│   ├── infrastructure.rst  # Infrastructure (cache, logger, etc.)
│   ├── platforms.rst   # Platform integrations (YouTube, Twitter)
│   └── utilities.rst   # Utility modules
├── _static/             # Static files (CSS, images)
├── _templates/          # Custom templates
└── _build/              # Generated documentation (gitignored)
```

## Documentation Style

This documentation uses:

- **Sphinx**: Documentation generator
- **ReadTheDocs Theme**: Clean, professional appearance
- **Napoleon Extension**: Support for Google-style docstrings
- **MyST Parser**: Support for Markdown files
- **Autodoc**: Automatic documentation from docstrings
- **Intersphinx**: Links to Python and Selenium docs

## Writing Documentation

### Docstrings

Follow the Google-style docstring format (see `docs/DOCSTRING_STYLE_GUIDE.md`):

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of the function.

    Longer description with more details about what the
    function does and how to use it.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is negative

    Example:
        >>> result = example_function("test", 42)
        >>> print(result)
        True
    """
    pass
```

### Adding New Modules

1. Add module to appropriate `.rst` file in `modules/`
2. Use `automodule` directive:

```rst
New Module
----------

.. automodule:: module_name
   :members:
   :undoc-members:
   :show-inheritance:
```

3. Rebuild documentation: `make html`

## Continuous Documentation

### GitHub Actions

Consider adding a GitHub Action to automatically build and deploy documentation:

```yaml
name: Documentation

on:
  push:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r docs/api/requirements-docs.txt
      - run: cd docs/api && make html
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: docs/api/_build/html
```

### ReadTheDocs

Alternatively, you can host on [ReadTheDocs](https://readthedocs.org/):

1. Create `.readthedocs.yaml` in project root
2. Connect repository to ReadTheDocs
3. Documentation builds automatically on commit

Example `.readthedocs.yaml`:

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.9"

sphinx:
  configuration: docs/api/conf.py

python:
  install:
    - requirements: docs/api/requirements-docs.txt
```

## Troubleshooting

### Import Errors

If you see import errors when building:

1. Ensure `src/` is in the Python path (configured in `conf.py`)
2. Check that all dependencies are installed
3. Verify module names in `.rst` files match actual module names

### Missing Docstrings

If documentation is incomplete:

1. Check for missing docstrings in source code
2. Ensure docstrings follow Google-style format
3. Run with verbose mode: `sphinx-build -v . _build/html`

### Theme Issues

If the theme doesn't render correctly:

```bash
pip install --upgrade sphinx-rtd-theme
make clean
make html
```

## Additional Resources

- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
- [Napoleon Extension](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [ReadTheDocs Theme](https://sphinx-rtd-theme.readthedocs.io/)
