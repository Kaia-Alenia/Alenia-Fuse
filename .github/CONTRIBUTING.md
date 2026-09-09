# Contributing to Alenia Fuse

Thank you for your interest in contributing to Alenia Fuse! This is an open-source project designed for the indie developer community and we are happy to receive your contributions.

## Getting Started
1. Fork this repository.
2. Clone your fork locally: `git clone https://github.com/YOUR-USERNAME/alenia-fuse.git`
3. Install dependencies and set up your local environment (we prefer `uv`).
4. Make your changes in a descriptive branch: `git checkout -b fix/my-fix` or `git checkout -b feat/new-feature`

## Code Structure
- **`src/alenia_fuse/media_engine.py`**: The core engine that wraps FFmpeg and handles media processing, Smart Caching, and Hardware Acceleration.
- **`src/alenia_fuse/`**: Core logic, utilities, and media processing.
- **`src/alenia_fuse/cli.py`**: The entry point for the application's GUI (Tkinter).
- **`cmd/ap/main.go`**: The CLI wrapper written in Go for ultra-fast execution in the terminal.

## Contribution Guidelines
- **Security first**: Ensure your code does not introduce vulnerabilities. We use Snyk in our CI/CD.
- **Testing**: Any major PR must include tests (pytest).
- **Formatting**: Run the linter and maintain visual consistency of the code.
- **Compatibility**: The tool must be able to run on Windows, Linux, and macOS seamlessly.

## Submitting a Pull Request
- Detail the changes you have made in your PR description.
- Ensure that GitHub Actions (build and snyk) pass successfully.
- An Alenia Studios maintainer will review and merge your code.

Thank you for supporting the indie ecosystem!
