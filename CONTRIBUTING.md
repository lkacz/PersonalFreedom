# Contributing to Personal Liberty

Thank you for your interest in contributing to Personal Liberty! We welcome contributions from the community to help make this the best focus and productivity tool.

## How to Contribute

### Reporting Bugs
If you find a bug, please open an issue on GitHub. Include:
- A clear title and description
- Steps to reproduce the issue
- Expected vs. actual behavior
- Screenshots (if applicable)
- Your operating system and Python version

### Suggesting Features
We love new ideas! Open an issue with the "enhancement" label to discuss your idea before implementing it.

### Pull Requests
1. **Fork the repository** and create your branch from `main`.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements_ai.txt
   pip install -e .[dev]
   ```
3. **Make your changes**. Ensure your code follows the project's style (we use `flake8` and `ruff`).
4. **Run tests**:
   ```bash
   pytest tests/
   ```
5. **Submit a Pull Request**. Describe your changes and link to any related issues.

## Development Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/lkacz/PersonalFreedom.git
   cd PersonalFreedom
   ```
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Install dependencies (see above).

## Code Style
- We use **PEP 8** guidelines.
- Type hints are encouraged (checked with `mypy`).
- Docstrings are required for new functions and classes.

## License
By contributing, you agree that your contributions will be licensed under the MIT License.
