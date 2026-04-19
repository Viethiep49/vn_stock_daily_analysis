# Testing Guide

This project uses `pytest` for testing. All tests are located in the `tests/` directory.

## Running Tests

To run the full test suite, use the following command from the project root:

```bash
pytest
```

### Verbose Output
For more detailed output, including each test case name:

```bash
pytest -v
```

### Filtering Tests
You can use markers defined in `pytest.ini` to filter tests.

#### Exclude Integration Tests
To run only unit tests and skip those that require an internet connection or external APIs:

```bash
pytest -m "not integration"
```

#### Run Only Integration Tests
To run only the integration tests:

```bash
pytest -m "integration"
```

## Directory Structure

The `tests/` directory mirrors the structure of some of the core modules for clarity:

- `test_analyzer.py`: Tests for `src/core/analyzer.py`.
- `test_circuit_breaker.py`: Tests for `src/market/circuit_breaker.py`.
- `test_data_provider.py`: Tests for `src/data_provider/`.
- `test_notifier.py`: Tests for `src/notifier/`.
- `test_scoring.py`: Tests for `src/scoring/`.
- `test_validator.py`: Tests for `src/utils/validator.py`.

## Configuration

Testing configuration is managed via `pytest.ini` in the project root. Key settings include:

- `testpaths`: Specifies `tests` as the directory for test discovery.
- `addopts`: Default command-line options (currently `-v --tb=short`).
- `markers`: Custom markers like `integration` for labeling specific test types.
