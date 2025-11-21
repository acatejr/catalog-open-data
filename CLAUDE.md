# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python tool (`catalog-open-data`) that fetches and catalogs USDA Forest Service ArcGIS REST API services. It retrieves service metadata from the Forest Service's ArcX REST services endpoint and compiles detailed information into a local catalog.

## Development Environment

- **Python Version**: 3.13+ (specified in `.python-version`)
- **Package Manager**: Uses `uv` for dependency management
- **Project Structure**: Standard Python package layout with source in `src/catalog_open_data/`

## Common Commands

### Running the application
```bash
# Install dependencies
uv sync

# Run the main catalog fetcher
uv run cod

# Or run directly via Python module
uv run python -m catalog_open_data
```

### Linting
```bash
# Run Ruff linter
uv run ruff check

# Run Ruff with auto-fix
uv run ruff check --fix

# Format code with Ruff
uv run ruff format
```

## Code Architecture

### Main Entry Point
The application has a single entry point defined in `pyproject.toml` as the `cod` command, which maps to `catalog_open_data:main`.

### Data Flow (src/catalog_open_data/main.py)
1. Fetches the root services index from `https://apps.fs.usda.gov/arcx/rest/services?f=pjson`
2. For each folder in the index, recursively fetches folder metadata
3. For each service within folders, fetches detailed MapServer metadata
4. Outputs complete catalog to `service_catalog.json`

### Key Dependencies
- **requests**: HTTP client for API calls (with rate limiting via requests-ratelimiter)
- **rich**: Terminal output formatting with color support
- **trafilatura**: Web content extraction (currently unused in main code)

## Code Style
- **Indentation**: 4 spaces (enforced by `.editorconfig`)
- **Linter**: Ruff is the configured linter/formatter
- **Trailing Whitespace**: Trimmed for all files except Markdown

## Notes
- The main script performs synchronous HTTP requests without rate limiting applied yet
- Error handling is present for the root request but commented out for nested requests (lines 46-78 in main.py)
- Output file is always `service_catalog.json` in the current directory
