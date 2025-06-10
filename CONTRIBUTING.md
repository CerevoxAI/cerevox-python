# Contributing to Cerevox Python SDK

Thank you for your interest in contributing to the Cerevox Python SDK! We welcome contributions from the community and are pleased to have you join us.

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title** for the issue to identify the problem
- **Describe the exact steps which reproduce the problem** in as many details as possible
- **Provide specific examples to demonstrate the steps**
- **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior
- **Explain which behavior you expected to see instead and why**
- **Include Python version, SDK version, and OS information**

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title** for the issue to identify the suggestion
- **Provide a step-by-step description of the suggested enhancement** in as many details as possible
- **Provide specific examples to demonstrate the steps**
- **Describe the current behavior** and **explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful** to most Cerevox SDK users

### Development Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/cerevox-python.git
   cd cerevox-python
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

5. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Making Changes

1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards:
   - Follow PEP 8 style guidelines
   - Add type hints to all functions and methods
   - Write docstrings for all public functions and classes
   - Add unit tests for new functionality
   - Ensure all tests pass

3. Run the test suite:
   ```bash
   pytest
   ```

4. Run code quality checks:
   ```bash
   black cerevox tests examples
   isort cerevox tests examples
   flake8 cerevox tests examples
   mypy cerevox
   ```

5. Commit your changes:
   ```bash
   git add .
   git commit -m "Add feature: your descriptive commit message"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Create a Pull Request on GitHub

### Coding Standards

#### Python Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Maximum line length: 88 characters

#### Type Hints
- Add type hints to all function signatures
- Use `typing` module for complex types
- Follow [PEP 484](https://www.python.org/dev/peps/pep-0484/) guidelines

#### Documentation
- Write docstrings for all public functions and classes
- Use [Google style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Include examples in docstrings where helpful

#### Testing
- Write unit tests for all new functionality
- Use `pytest` for testing framework
- Aim for high test coverage (>80%)
- Include both sync and async test cases where applicable
- Use descriptive test names

### Pull Request Guidelines

- Fill in the required template
- Do not include issue numbers in the PR title
- Include screenshots and animated GIFs in your pull request whenever possible
- Follow the Python and documentation styleguides
- Include thoughtfully-worded, well-structured tests
- Document new code based on the Documentation Styleguide
- End all files with a newline

### Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=cerevox --cov-report=html

# Format code
black cerevox tests examples
isort cerevox tests examples

# Lint code
flake8 cerevox tests examples
mypy cerevox

# Build package
python -m build

# Install pre-commit hooks
pre-commit install
```

### Documentation

- Keep the README.md updated with any new features
- Update docstrings when modifying functions
- Add examples to the `examples/` directory for significant new features

## Getting Help

If you need help, you can:

- Open an issue on GitHub
- Contact us at support@cerevox.ai
- Check our documentation at https://docs.cerevox.ai

Thank you for contributing to Cerevox Python SDK! 