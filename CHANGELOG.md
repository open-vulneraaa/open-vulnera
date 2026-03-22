# Changelog

## [0.1.2] - 2026-03-22
### Added
- `vulnera/core/utils/session_manager.py`: session state persistence and attack phase inference.
- `vulnera/core/utils/rag_manager.py`: RAG history storage and retrieval for post-recon analysis.

### Fixed
- `vulnera/core/computer/terminal/languages/subprocess_language.py`: default start command handling for shells (`bash`/`cmd.exe`) to avoid startup `list index out of range` in tests.
- `vulnera/core/respond.py`: hallucination resilience for `functions.execute({...})` payload extraction and JSON wrapper parsing.
- `vulnera/core/core.py`: `conversation_state` sync to session manager on state updates.
- `vulnera/core/computer/terminal/languages/shell.py`: blocking complex/unsafe shell syntax to prevent hallucinated command execution.

### Testing
- `tests/test_vulnera.py`: new regression tests for session manager and RAG manager, plus existing hallucination/shell-timeout checks.
- Full suite run: 21 passed, 9 failed (existing non-related server/async tests already in repo). 

## [0.1.1] - Previous
- Prior release state, baseline.
