# Contributing to VN Stock Daily Analysis

Thank you for your interest in contributing to this project!

## Pull Request Process

1. **Create an Issue:** Before starting any work, please open an issue to discuss your proposed changes.
2. **Branching:** Create a new branch for your feature or bugfix (e.g., `feat/my-feature` or `fix/issue-id`).
3. **Tests:** Ensure all tests pass and add new tests for your changes.
4. **Pull Request:** Open a PR against the `main` branch. Provide a clear description of the changes.
5. **Review:** Wait for feedback and address any review comments.

## Coding Standards

- **Language:** Python 3.11+.
- **Formatting:** Follow PEP 8. Use `autopep8` or `black` for formatting.
- **Linting:** Code must pass `flake8` checks. Max line length is 120.
- **Naming:** Use `snake_case` for functions/variables and `PascalCase` for classes.
- **Documentation:** Use docstrings for all public functions, classes, and modules.
- **Types:** Use type hints for function arguments and return values.

## Testing Guidelines

- Use `pytest` for all tests.
- Place tests in the `tests/` directory.
- Aim for high test coverage for new logic.
- Run tests with: `PYTHONPATH=. pytest tests/ -v`

## Project Structure

- `src/core/`: Orchestration and core logic.
- `src/data_provider/`: Data fetching interfaces.
- `src/market/`: Market-specific logic (circuit breakers, sector mapping).
- `src/notifier/`: Notification bots (Telegram, Discord).
- `src/strategies/`: YAML-based trading strategies.
- `src/utils/`: Shared utilities and validators.
