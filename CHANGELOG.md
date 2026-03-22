# Changelog

## [0.1.3] - 2026-03-22
### Fixed
- Standardized class naming: `AsyncInterpreter` to `AsyncVulnera` for project consistency.
- Updated variable names in the async core module for clarity.
- Refreshed imports, tests, and documentation to align with the new class name.
- Eliminated deprecated `INTERPRETER_` environment variable fallbacks, standardizing on `VULNERA_` prefixes.

## [0.1.2] - 2026-03-22
### Added
- `vulnera/core/utils/session_manager.py`: New module for session state persistence and attack phase inference, enabling conversation continuity across sessions.
- `vulnera/core/utils/rag_manager.py`: New module for RAG (Retrieval-Augmented Generation) history storage and retrieval, supporting post-recon analysis and knowledge reuse.

### Fixed
- `vulnera/core/computer/terminal/languages/subprocess_language.py`: Improved default start command handling for shells (`bash` on Unix, `cmd.exe` on Windows) to prevent `list index out of range` errors in tests and direct usage.
- `vulnera/core/respond.py`: Enhanced hallucination resilience with support for `functions.execute({...})` payload extraction and JSON wrapper parsing.
- `vulnera/core/core.py`: Synchronized `conversation_state` with session manager on state updates for persistent state management.
- `vulnera/core/computer/terminal/languages/shell.py`: Strengthened blocking of complex/unsafe shell syntax to prevent execution of hallucinated commands.

### Testing
- `tests/test_vulnera.py`: Added new regression tests for session manager and RAG manager functionality.
- Maintained existing tests for hallucination handling, shell preprocessing, and subprocess timeouts.
- Full test suite results: 21 passed, 9 failed (failures are in server-related tests requiring optional dependencies like `fastapi` and `websockets`, not affecting core functionality).

## [0.1.1] - 2026-03-22
### Fixed
- `vulnera/terminal_interface/start_terminal_interface.py`: Resolved issue where `-y` flag bypassed message append and system prompt injection.
- `vulnera/core/default_system_message.py`: Updated system message handling to ensure proper prompt construction.
- `vulnera/core/computer/terminal/languages/subprocess_language.py`: Implemented robust process control with fixed 5-minute timeouts, proper termination, and abort handling to prevent hangs.
- `vulnera/core/computer/terminal/languages/shell.py`: Added safe shell command preprocessing to block complex syntax hallucinations and unsafe command execution.
- `vulnera/core/respond.py`: Integrated conversation state injection into LLM system prompts for context awareness.
- `vulnera/core/core.py`: Added conversation state management and persistence mechanisms.

### Testing
- `tests/test_vulnera.py`: Introduced regression tests for shell safety, command timeouts, and stateful prompt behavior.

## [0.1.0] - Previous
- Initial release with core functionality.
