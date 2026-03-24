# Contributing to agent-cache

Thank you for your interest in improving **agent-cache**! All contributions — bug reports, feature requests, documentation fixes, and code — are welcome.

---

## Development Setup

```bash
git clone https://github.com/example/agent-cache
cd agent-cache

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in editable mode (zero runtime deps)
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

---

## Code Style

- **Python ≥ 3.10** required.
- Type annotations on all public APIs.
- Docstrings on all public classes and methods (Google style).
- Maximum line length: 100 characters.
- No runtime dependencies — the library must stay zero-dep.

---

## Pull Request Guidelines

1. Fork the repository and create a feature branch (`git checkout -b feat/my-feature`).
2. Add or update tests to cover your change.
3. Ensure `python -m pytest tests/ -v` passes with **zero failures**.
4. Write a clear PR description explaining *what* and *why*.
5. Update `CHANGELOG.md` under the `[Unreleased]` section.

---

## Reporting Bugs

Open an issue with:
- Python version and OS.
- Minimal reproducible example.
- Expected vs. actual behaviour.

---

## Security

See [SECURITY.md](SECURITY.md) for responsible disclosure guidelines.
