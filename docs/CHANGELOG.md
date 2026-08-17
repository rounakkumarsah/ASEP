# Changelog — OpenSEP
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-RC1] — 2026-08-17

### Added
- Created unified health check instrumentation inside backend app initialization routines.
- Implemented isolated mock session detail response mechanisms for test executions.

### Fixed
- Resolved Next.js frontend standalone output compilation build errors.
- Added missing dependencies `pg8000` and `langgraph` to requirements config.
- Corrected Alembic migration script enum type duplication.
- Updated Playwright login and signup Page Object Models (POMs) selectors to align with redesigned landing screens.
- Corrected terminal emulator specs selector timeout assertions.

### Changed
- Refactored E2E specs assertions checking breadcrumb headings instead of strict heading elements.
