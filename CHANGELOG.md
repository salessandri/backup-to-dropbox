# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-10-04

### Added

- Migrated from setup.py to pyproject.toml and uv package management system for better dependency management and modern Python packaging standards

### Changed

- Updated Dropbox library dependency to latest version for improved compatibility and security
- Restructured project layout by moving the main module under `src/` folder for better organization
- Added `uv.lock` file to version control for reproducible builds

### Fixed

- None

### Deprecated

- None

### Removed

- None

### Security

- Updated Dropbox library dependency addresses potential security vulnerabilities in the previous version

## [0.2.0] - 2023-12-19

Previous release with package metadata updates and project restructuring.

## [0.1.1] - 2023-12-18

Bug fix release.

## [0.1.0] - 2023-12-17

Initial release with basic backup functionality, GPG encryption support, and Dropbox integration.
