# Contributing to Alexa AirPlay Bridge

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional. We welcome all skill levels!

## Ways to Contribute

### 1. Report Bugs
- Check [existing issues](https://github.com/yourusername/alexa-airplay-addon/issues) first
- Provide clear description and reproduction steps
- Include relevant logs (sanitized of sensitive info)
- System info (Home Assistant version, hardware, etc.)

### 2. Suggest Features
- Create an issue with "enhancement" label
- Describe the feature clearly
- Explain use cases and benefits
- Reference related issues or PRs

### 3. Improve Documentation
- Fix typos and unclear sections
- Add examples and diagrams
- Improve troubleshooting guides
- Translate to other languages

### 4. Submit Code

#### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/alexa-airplay-addon.git
cd alexa-airplay-addon

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # development tools

# Run tests
python -m pytest tests/

# Run linting
flake8 app/
pylint app/

# Format code
black app/
```

#### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

2. **Make changes**
   - Follow Python PEP8 style guide
   - Add docstrings to functions/classes
   - Add tests for new functionality
   - Update documentation

3. **Test locally**
   ```bash
   # Run unit tests
   python -m pytest tests/
   
   # Check code quality
   flake8 app/
   pylint app/
   
   # Format code
   black app/
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "Clear description of changes"
   # Good: "Add volume control for AirPlay devices"
   # Bad: "fix stuff"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Go to GitHub
   - Click "Compare & pull request"
   - Fill out PR template
   - Request review

#### PR Guidelines

- One feature/fix per PR
- Clear title and description
- Reference related issues
- Update documentation
- Include tests
- No breaking changes without discussion

#### Code Style

**Python**:
```python
# Use type hints
def get_device(self, device_id: str) -> Optional[VirtualDevice]:
    """Get a device by ID.
    
    Args:
        device_id: The unique device ID
        
    Returns:
        The device object or None if not found
    """
    pass

# Use descriptive names
device_manager = DeviceManager()  # Good
dm = DeviceManager()  # Bad

# Add comments for complex logic
# Update tokens before making API call to ensure freshness
if needs_token_refresh:
    await refresh_token()
```

**Documentation**:
- Use clear, concise language
- Include code examples
- Add links to related sections
- Keep formatting consistent

### 5. Testing

#### Add Tests

```python
# tests/test_device_manager.py
import pytest
from app.core.device_manager import DeviceManager, PlaybackState


class TestDeviceManager:
    def test_get_device(self):
        manager = DeviceManager(None, None)
        device = manager.get_device("test_id")
        assert device is None  # No device yet
    
    def test_set_volume(self):
        # Create mock device
        # Test volume setting
        pass
```

Run tests:
```bash
pytest tests/ -v
pytest tests/ --cov=app  # with coverage
```

## Development Checklist

Before submitting PR, ensure:

- [ ] Code follows PEP8 style guide
- [ ] All tests pass: `pytest tests/`
- [ ] No linting errors: `flake8 app/`
- [ ] Docstrings added to new functions
- [ ] Documentation updated
- [ ] No sensitive info in commits
- [ ] Commit messages are clear
- [ ] One feature/fix per PR

## Release Process

Maintainers only:

1. Update version in `app/version.py`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.1`
4. Push tag: `git push origin --tags`
5. Create GitHub release
6. Build Docker image
7. Push to Docker registry

## Areas for Contribution

### High Priority
- [ ] AirPlay 2 protocol support
- [ ] Performance optimization
- [ ] More comprehensive testing
- [ ] Windows support
- [ ] HomeKit integration

### Medium Priority
- [ ] Additional music service integrations
- [ ] Web UI improvements
- [ ] Automation examples
- [ ] Translations
- [ ] Docker Compose setup

### Low Priority
- [ ] Documentation improvements
- [ ] README examples
- [ ] Troubleshooting additions
- [ ] Community forum responses

## Questions?

- 💬 Ask in [Discussions](https://github.com/yourusername/alexa-airplay-addon/discussions)
- 📧 Email: maintainer@example.com
- 🐛 Report bugs: [Issues](https://github.com/yourusername/alexa-airplay-addon/issues)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing! 🙏
