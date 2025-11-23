# Repository Guidelines

## Project Structure & Module Organization
The runtime code lives in `src/catalog_open_data/`; `main.py` holds the CLI entrypoint exposed as `cod`. Generated artifacts (service catalogs and interim JSON dumps) belong in `data/`, which is already ignored for bulk outputs. Reference notes live in `requests-ratelimiter-plan.md`, and dependency metadata is tracked in `pyproject.toml` plus `uv.lock`. Keep future modules under `src/catalog_open_data/` with descriptive package names, and mirror that structure inside any future `tests/` tree to keep imports straightforward.

## Build, Test, and Development Commands
- `uv sync` (or `pip install -e .[dev]`) installs runtime plus dev dependencies.
- `uv run cod` executes the packaged CLI and writes `data/service_catalog.json`.
- `uv run ruff check` lints all Python modules; add `--fix` only when the diff is easy to review.
- `pytest` (once tests exist) should be invoked from the repo root; prefer `pytest -k <module>` for targeted runs during triage.

## Coding Style & Naming Conventions
Target Python 3.14, four-space indentation, and type hints on all public functions. Module names stay lowercase with underscores (`catalog_open_data/fetchers.py`), and functions should read as verbs (`fetch_folder_index`). Use `ruff` to enforce PEP 8 plus project defaults; run it before submitting code. Keep print-style diagnostics routed through `rich.print` for consistent coloring.

## Testing Guidelines
Adopt `pytest` with a `tests/` directory that mirrors `src/`. Name files `test_<module>.py` and use fixtures to stub network calls so USDA APIs are never hit in CI. For data-heavy scenarios, check in minimal JSON fixtures under `tests/fixtures/`. Measure coverage with `pytest --cov=catalog_open_data` and aim for ≥85% on any new module.

## Commit & Pull Request Guidelines
Recent history favors short, imperative summaries (“Updated ignore files”, “Config update”). Follow that pattern, keep the first line ≤72 characters, and reference issues using `Refs #123` in the body when relevant. Every pull request should describe the problem, the solution, and validation steps (commands, screenshots of console output, or sample JSON). Link to produced data under `data/` only when sanitized, and flag breaking API changes prominently so downstream automations can adapt.

## Security & Configuration Tips
Never commit raw service dumps or secrets; `.env*` is ignored—store credentials there if future endpoints require them. Treat `data/service_catalog.json` as disposable cache and redact sensitive fields before sharing externally. Use `requests-ratelimiter` (already planned) when scripting high-volume harvests to avoid throttling, and document any new environment variables in `README.md` plus `.env.example`.
