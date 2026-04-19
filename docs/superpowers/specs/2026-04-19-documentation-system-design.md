# Design Spec: Comprehensive Documentation System

**Date:** 2026-04-19
**Topic:** Documentation System for VN Stock Daily Analysis
**Status:** Approved

## 1. Overview
The goal is to create a multi-layered documentation system in English, catering to both end-users (investors/users) and developers (contributors/maintainers). The documentation will be stored in a dedicated `docs/` folder, structured for clarity and maintainability.

## 2. Target Audience
- **End-Users:** People looking to install, configure, and use the bot to receive stock analysis.
- **Developers:** People looking to understand the internal architecture, extend functionality (add data providers, strategies), or fix bugs.

## 3. Documentation Structure

### 3.1 User Documentation (`docs/user/`)
Focuses on setup and operation.
- `getting-started.md`: Installation, environment setup, and a first-run guide.
- `configuration.md`: Deep dive into `.env` settings, LLM provider setup (Gemini, OpenAI), and notification channels (Telegram, Discord).
- `usage-guide.md`: CLI commands, GitHub Actions automation, and basic troubleshooting.

### 3.2 Developer Documentation (`docs/dev/`)
Focuses on internals and extensibility.
- `architecture.md`: High-level system design with Mermaid diagrams showing data flows (Data -> Analyzer -> AI -> Notifier).
- `strategy-customization.md`: Guide on how to write/modify YAML strategy files and how they influence the AI prompts.
- `api-reference.md`: Breakdown of the core modules (`src/core`, `src/data_provider`, `src/scoring`, etc.).
- `testing.md`: How to run, maintain, and write new tests.

### 3.3 Root Documentation
- `CONTRIBUTING.md`: Rules for contribution, branch naming, and PR process.
- `README.md` (Update): Keep it as the main entry point, with links to the full documentation in `docs/`.

## 4. Technical Requirements
- **Language:** English.
- **Format:** Markdown (`.md`).
- **Visuals:** Mermaid diagrams for architecture.
- **Translation:** Porting existing Vietnamese content from current README and comments into English documentation.

## 5. Success Criteria
- A user can set up the bot from scratch using only the documentation.
- A developer can understand the core components and add a new strategy or notifier.
- All documents follow a consistent style and are linked together.
