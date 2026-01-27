# TODO

- [ ] Ask agent to
  - [x] Change settings so I can use local ollama with antigravity (currently not possible)
  - [x] Write a nice summary of how the subsystems are tested
  - [x] draw a system architecture diagram containing the major subsystems like ACE
  - [ ] Fix the python language server settings so it stops crashing (installing a different one is ok)
- [x] Ask agent about including "Knowledge" artifacts: mirrors "learnings" or "lessons learned" in current framework? (currently does not seem to be supported, support ticket filed)

- [x] there's a bug that causes the screen to flash white when the page is reloaded. there should be no flash for either light or dark mode (this issue might already be in beads. If so, it just needs the additional information upserted into it.

can you please write a python script to copy the lines you need from the log file?  I would like to eliminate ANY copy/pasting possible.  Also, can you now drive the UI tests yourself? I would like to make this entire process as automated as possible. For testing, I would recommend any of the files in the test documents folder that are under 50 bytes. They take about a minute and a half to upload and process. Please add global rules about trying to make all testing as automated as possible, including by implementing different log levels.

Python's logging module defines six standard log levels, each associated with a unique integer value indicating the severity of the message.
The standard levels, in order of increasing severity, are:
Level  Numeric Value Description
NOTSET 0 Indicates to consult ancestor loggers to determine the effective level. If the root is also NOTSET, all messages are logged.
DEBUG 10 Detailed diagnostic information, useful for development or troubleshooting.
INFO 20 Confirms expected operations or provides general program flow information.
WARNING 30 Indicates a potential issue that doesn't halt software operation. This is the default level.
ERROR 40 Signals a more significant issue where a function could not be performed.
CRITICAL 50 Represents a serious error that may prevent the program from continuing.
When a logging level is set, only messages at that level or higher are recorded or displayed.

How to Use
You can configure the logging level using `logging.basicConfig()`:

```python
import logging

# Set the minimum level to log to INFO and above
logging.basicConfig(level=logging.INFO)

logging.debug("This message will be ignored by the default configuration")
logging.info("This is an informational message, and it will be logged")
logging.warning("This is a warning message")
```

For more details, refer to the Python documentation.
