# Contributing to Alenia Fuse

Thank you for your interest in contributing to Alenia Fuse! This is an open-source project designed for the indie developer community and we are happy to receive your contributions.

## How to get started
1. Fork this repository.
2. Clone your fork locally: `git clone https://github.com/YOUR-USER/alenia-fuse.git`
3. Install the dependencies and create your local environment (we prefer `uv`).
4. Make your changes in a descriptive branch: `git checkout -b fix/my-fix` or `git checkout -b feat/new-feature`

## Code Structure
- **`src/fuse/media_engine.py`**: The core engine wrapping FFmpeg and handling media processing, Smart Caching and Hardware Acceleration.
- **`src/fuse/`**: Core logic, utilities and multimedia processing.
- **`src/fuse/cli.py`**: The entry point for the GUI (Tkinter) of the application.
- **`src/fuse/cli/`**: The implementation of the CLI and its public commands.

## Contribution Rules
- **Security first**: Ensure your code does not introduce vulnerabilities. We use Snyk in our CI/CD.
- **Testing**: Any major PR must include tests (pytest).
- **Format**: Run the linter and maintain visual consistency of the code.
- **Compatibility**: The tool must be able to run on Windows, Linux and macOS without issues.

## Submitting a Pull Request
- Detail the changes you have made in the description of your PR.
- Ensure that GitHub Actions (build and snyk) pass successfully.
- An Alenia Studios maintainer will review and merge your code.

Thank you for supporting the indie ecosystem!
