# TODO Tasks & Backlog

This file contains project-wide TODO items and tasks that need attention from any agent working on this repository.

## Current TODO Items

### Development Environment Setup
- [ ] Fix Python language server settings to prevent crashes (installing a different one is ok)

### Automation & Testing Improvements
- [ ] Write Python script to automatically copy needed lines from log files to eliminate copy/pasting
- [ ] Implement automated UI testing drive capability
- [ ] Use test documents under 50 bytes for testing (take ~1.5 minutes to upload/process)
- [ ] Add global rules about making testing as automated as possible
- [ ] Implement different log levels for better debugging

### Bug Fixes
- [x] Change settings to allow local ollama with antigravity (completed)
- [x] Write summary of how subsystems are tested (completed)
- [x] Draw system architecture diagram with major subsystems like ACE (completed)
- [x] Include "Knowledge" artifacts support (support ticket filed)
- [x] Fix white flash screen reload issue for light/dark mode (may need beads update)

## Logging Standards

Python's logging module defines six standard log levels, each associated with a unique integer value indicating the severity of the message:

| Level | Numeric Value | Description |
|-------|---------------|-------------|
| NOTSET | 0 | Indicates to consult ancestor loggers to determine the effective level |
| DEBUG | 10 | Detailed diagnostic information, useful for development or troubleshooting |
| INFO | 20 | Confirms expected operations or provides general program flow information |
| WARNING | 30 | Indicates a potential issue that doesn't halt software operation (default) |
| ERROR | 40 | Signals a more significant issue where a function could not be performed |
| CRITICAL | 50 | Represents a serious error that may prevent the program from continuing |

### Usage Example

```python
import logging

# Set the minimum level to log to INFO and above
logging.basicConfig(level=logging.INFO)

logging.debug("This message will be ignored by the default configuration")
logging.info("This is an informational message, and it will be logged")
logging.warning("This is a warning message")
```

## Notes for Future Agents

- Always check this file for outstanding tasks before starting new work
- Update items as they are completed or new tasks are identified
- Consider automation opportunities in all development work
- Follow proper logging standards for better debugging and monitoring
