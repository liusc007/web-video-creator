# Contributing to web-video-creator

Thank you for your interest in contributing to `web-video-creator`! We welcome contributions of all kinds: bug fixes, new cinematic HUD templates, audio spatial presets, performance optimizations, and documentation improvements.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/web-video-creator.git
   cd web-video-creator
   ```

2. **Set up a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   playwright install chromium
   ```

3. **Run the test suite:**
   ```bash
   pytest tests/
   ```

## Contribution Workflow

1. Create a feature branch (`git checkout -b feature/amazing-hud-preset`).
2. Implement your changes with clean, well-documented code.
3. Add unit tests for your changes in `tests/`.
4. Ensure all tests pass.
5. Commit your changes with conventional commit messages (`feat: ...`, `fix: ...`, `docs: ...`).
6. Push to your branch and open a Pull Request.

## Code Style
- Follow PEP 8 guidelines.
- Keep HTML/CSS templates clean, responsive (1080p native target), and modern.
- All new features should have corresponding unit tests.
