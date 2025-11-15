# Affinity CLI - Personal Project Policy

Thank you for your interest in Affinity CLI! This document explains how the community can engage with this project.

## 📋 Project Status: Personal Project

**Affinity CLI is a personal project maintained solely by ind4skylivey.**

This means:
- ✅ **You CAN:** Use the software freely
- ✅ **You CAN:** Report bugs and issues
- ✅ **You CAN:** Request features and improvements
- ✅ **You CAN:** Share and promote the project
- ❌ **You CANNOT:** Submit code contributions (pull requests)
- ❌ **You CANNOT:** Modify or redistribute modified versions

## 🎯 Why This Policy?

This is a **personal learning and development project** where I want to:
- Maintain full control over the codebase architecture
- Learn and implement features myself
- Keep a consistent coding style and approach
- Take full responsibility for all code quality

## 💬 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (commands you ran, output you got)
- **Describe the behavior you observed and what you expected**
- **Include system information** (run `affinity-cli report --output report.json`)
- **Include screenshots** if relevant

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the proposed enhancement
- **Explain why this enhancement would be useful**
- **List some examples** of how it would be used

### Code Contributions

**Please note:** This project does not accept external code contributions (pull requests).

If you have coding suggestions or improvements, please:
1. Open a detailed issue describing your idea
2. Explain the problem it solves
3. Provide examples or pseudocode if helpful
4. I will review and may implement it myself

## Testing Locally (For Your Own Use)

If you want to test the software or experiment with it locally:

```bash
# Clone the repository
git clone https://github.com/ind4skylivey/affinity-cli.git
cd affinity-cli

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Run and test
affinity-cli --help
```

**Note:** Any modifications you make are for your personal use only and cannot be distributed.

## Coding Standards

### Python Style

- Follow **PEP 8** guidelines
- Use **type hints** for function parameters and returns
- Write **docstrings** for all classes and functions (Google style)
- Keep lines under **100 characters** where reasonable
- Use **meaningful variable names**

### Example

```python
def install_dependency(package_name: str, version: Optional[str] = None) -> Tuple[bool, str]:
    """
    Install a system dependency.
    
    Args:
        package_name: Name of the package to install
        version: Specific version to install (optional)
    
    Returns:
        Tuple of (success, message)
    """
    # Implementation
    pass
```

### Code Organization

- **Core functionality** goes in `affinity_cli/core/`
- **CLI commands** go in `affinity_cli/commands/`
- **Utilities** go in `affinity_cli/utils/`
- **Tests** go in `tests/` with `test_` prefix

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- First line is a summary (50 chars or less)
- Reference issues and PRs when relevant

**Examples:**
```
Add support for Ubuntu 24.04
Fix Wine detection on Fedora 40
Update dependency manager for better error handling
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_distro_detector.py -v

# Run with coverage
pytest tests/ --cov=affinity_cli --cov-report=html
```

### Writing Tests

- Write tests for all new functionality
- Aim for **70%+ code coverage**
- Use **descriptive test names**
- Test both success and failure cases

### Test Structure

```python
class TestFeatureName:
    """Test FeatureName class"""
    
    def test_specific_functionality(self):
        """Test that specific functionality works correctly"""
        # Arrange
        manager = FeatureName()
        
        # Act
        result = manager.do_something()
        
        # Assert
        assert result is not None
```

## Distribution Support

When adding support for a new Linux distribution:

1. Add distro to `DISTRO_MAPPING` in `distro_detector.py`
2. Add dependencies to appropriate method in `dependency_manager.py`
3. Test on actual distribution (VM or container)
4. Update documentation (README.md and docs/)

## Documentation

- Update **README.md** for user-facing changes
- Update **docstrings** for code changes
- Add examples for new features
- Keep documentation clear and concise

## Community

- Be patient and respectful in discussions
- Help others when you can
- Share your success stories
- Spread the word about Affinity on Linux

## Recognition

Helpful community members will be recognized:
- In the project README (for valuable feedback/testing)
- In release notes (when their suggestions are implemented)
- Special thanks section for significant contributions to ideas

## Questions?

Feel free to open an issue with the `question` label, or reach out through GitHub discussions.

---

**Thank you for contributing to making Linux a first-class platform for creative professionals!** 🐧🎨
