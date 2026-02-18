# Contributing to DroneSecurity Windows Port

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)
7. [Coding Standards](#coding-standards)
8. [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:
- Experience level
- Gender identity and expression
- Sexual orientation
- Disability
- Personal appearance
- Body size
- Race
- Ethnicity
- Age
- Religion
- Nationality

### Expected Behavior

- Be respectful and considerate
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept responsibility for mistakes
- Prioritize the community's best interests

### Unacceptable Behavior

- Harassment, discrimination, or offensive comments
- Personal attacks or trolling
- Publishing others' private information
- Spam or off-topic discussions

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:
- Git installed
- Python 3.8+ installed
- GNU Radio 3.10+ installed
- BladeRF A4 or USRP B205-mini (for hardware testing)
- Familiarity with signal processing concepts

### Finding Issues to Work On

1. **Check GitHub Issues:** https://github.com/Skeletoskull/DroneSecurity/issues
2. **Look for labels:**
   - `good first issue` - Suitable for beginners
   - `help wanted` - Maintainers need assistance
   - `bug` - Bug fixes needed
   - `enhancement` - New features
   - `documentation` - Documentation improvements

3. **Comment on the issue** to let others know you're working on it

---

## Development Setup

### 1. Fork the Repository

```bash
# Go to: https://github.com/Skeletoskull/DroneSecurity
# Click "Fork" button
```

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/DroneSecurity.git
cd DroneSecurity
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/Skeletoskull/DroneSecurity.git
git remote -v
```

### 4. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov hypothesis black flake8 mypy
```

### 6. Verify Setup

```bash
# Run tests
pytest

# Test offline decoder (no hardware needed)
python src/droneid_receiver_offline.py -i samples/mini2_sm
```

---

## Making Changes

### 1. Create a Feature Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch naming conventions:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_your_feature.py

# Run with coverage
pytest --cov=src tests/

# Check code style
flake8 src/ tests/
black --check src/ tests/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "Add feature: brief description

Detailed explanation of what changed and why.

Fixes #123"
```

**Commit message guidelines:**
- Use present tense ("Add feature" not "Added feature")
- First line: brief summary (50 chars max)
- Blank line
- Detailed explanation (wrap at 72 chars)
- Reference issues: "Fixes #123" or "Closes #456"

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_frequency_scanner.py

# Specific test function
pytest tests/test_frequency_scanner.py::test_frequency_locking

# With verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=html tests/
```

### Writing Tests

**Test file structure:**
```python
import pytest
from src.your_module import YourClass

def test_your_function():
    """Test description."""
    # Arrange
    input_data = ...
    
    # Act
    result = your_function(input_data)
    
    # Assert
    assert result == expected_value
```

**Property-based testing (Hypothesis):**
```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.integers(min_value=0, max_value=60))
def test_gain_setting(gain):
    """Test gain setting with various values."""
    receiver = BladeRFReceiver(gain=gain)
    assert receiver.gain == gain
```

### Test Coverage

- Aim for > 80% code coverage
- Test edge cases and error conditions
- Test both success and failure paths

---

## Submitting Changes

### 1. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 2. Create Pull Request

1. Go to your fork on GitHub
2. Click "Pull Request" button
3. Select your feature branch
4. Fill in the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Tested on Windows
- [ ] Tested on Linux
- [ ] Tested with hardware

## Checklist
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #123
```

### 3. Code Review Process

- Maintainers will review your PR
- Address feedback and make requested changes
- Push updates to the same branch
- PR will be merged when approved

### 4. After Merge

```bash
# Update your fork
git checkout main
git pull upstream main
git push origin main

# Delete feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

---

## Coding Standards

### Python Style

**Follow PEP 8:**
- 4 spaces for indentation (no tabs)
- 79 characters per line (code)
- 72 characters per line (comments)
- 2 blank lines between top-level functions/classes
- 1 blank line between methods

**Use Black formatter:**
```bash
black src/ tests/
```

**Use Flake8 linter:**
```bash
flake8 src/ tests/
```

### Type Hints

Use type hints for function signatures:

```python
def process_samples(samples: np.ndarray, sample_rate: float) -> bool:
    """Process IQ samples.
    
    Args:
        samples: Complex64 IQ samples
        sample_rate: Sample rate in Hz
        
    Returns:
        True if successful, False otherwise
    """
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_offset(signal: np.ndarray, fs: float) -> tuple[float, bool]:
    """Calculate frequency offset from signal.
    
    Args:
        signal: Input signal samples
        fs: Sample rate in Hz
        
    Returns:
        Tuple of (offset in Hz, success flag)
        
    Raises:
        ValueError: If signal is too short
        
    Example:
        >>> offset, success = calculate_offset(samples, 50e6)
        >>> if success:
        ...     print(f"Offset: {offset} Hz")
    """
    ...
```

### Error Handling

```python
# Good: Specific exceptions
try:
    receiver = BladeRFReceiver()
except DeviceNotFoundError as e:
    logger.error(f"BladeRF not found: {e}")
    sys.exit(1)

# Bad: Bare except
try:
    receiver = BladeRFReceiver()
except:
    pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed diagnostic information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.critical("Critical errors")
```

---

## Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Comment complex algorithms
- Explain "why" not "what" in comments

### User Documentation

When adding features, update:
- **README.md** - If it affects quick start
- **QUICK_REFERENCE.md** - If adding new commands
- **FAQ.md** - If addressing common questions
- **INSTALLATION_GUIDE_*.md** - If changing dependencies
- **CHANGELOG_WINDOWS_PORT.md** - Always update

### Documentation Style

- Use clear, concise language
- Provide examples
- Include command-line examples
- Add screenshots for GUI features
- Keep formatting consistent

---

## Types of Contributions

### Bug Fixes

1. Create issue describing the bug
2. Include steps to reproduce
3. Provide error messages
4. Submit PR with fix
5. Add test to prevent regression

### New Features

1. Create issue proposing the feature
2. Discuss design with maintainers
3. Implement feature
4. Add tests
5. Update documentation
6. Submit PR

### Documentation

1. Identify documentation gaps
2. Write clear, helpful content
3. Add examples
4. Submit PR

### Performance Improvements

1. Profile code to identify bottlenecks
2. Implement optimization
3. Benchmark before/after
4. Ensure no functionality changes
5. Submit PR with benchmark results

### Hardware Support

1. Propose new SDR support
2. Implement hardware interface
3. Test thoroughly
4. Document setup process
5. Submit PR

---

## Questions?

- **GitHub Issues:** https://github.com/Skeletoskull/DroneSecurity/issues
- **Discussions:** https://github.com/Skeletoskull/DroneSecurity/discussions
- **Email:** (if provided)

---

## License

By contributing, you agree that your contributions will be licensed under the AGPL-3.0 license.

---

**Thank you for contributing to DroneSecurity!** 🎉
