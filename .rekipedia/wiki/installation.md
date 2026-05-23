---
slug: installation
title: "Installation Instructions"
section: getting-started
tags: [getting-started, configuration]
pin: false
importance: 80
created_at: 2026-05-23T04:36:23Z
rekipedia_version: 0.17.15
---

# Installation Instructions

Welcome to the installation guide for the `pytk-cli` and `pytk-vscode` projects. This document will provide detailed instructions on how to install and configure these tools, ensuring a smooth setup process.

## Prerequisites

Before you begin the installation, ensure that your system meets the following prerequisites:

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: Version 3.7 or higher
- **Node.js**: Version 12 or higher (for `pytk-vscode`)

### Required Tools

- **pip**: Python package installer
- **npm**: Node package manager (for `pytk-vscode`)
- **git**: Version control system

### Dependencies

Ensure that you have the following dependencies installed:

- **build**: Python package for building distributions
- **twine**: Python package for uploading distributions to PyPI

You can install these dependencies using pip:
```bash
pip install build twine
```

> **Sources:** `pyproject.toml`

## Installation Steps

### Python Package (`pytk-cli`)

To install the `pytk-cli` package, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/pytk-cli.git
   cd pytk-cli
   ```

2. **Install the Package**
   ```bash
   pip install .
   ```

3. **Build the Package**
   ```bash
   python -m build
   ```

4. **Upload to PyPI (optional)**
   ```bash
   twine upload dist/*
   ```

### VS Code Extension (`pytk-vscode`)

To install the `pytk-vscode` extension, follow these steps:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/pytk-vscode.git
   cd pytk-vscode
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Build the Extension**
   ```bash
   npm run build
   ```

4. **Install the Extension Locally**
   ```bash
   code --install-extension ./pytk-vscode-0.1.0.vsix
   ```

> **Sources:** `pyproject.toml` · `vscode-extension/package.json`

## Configuration

### Python Package Configuration

The `pytk-cli` package uses a configuration file to manage settings. The configuration file can be located in the project directory or user directory. The configuration options include:

| Option          | Default Value | Description                                      |
|-----------------|----------------|--------------------------------------------------|
| `cache_enabled` | `true`         | Enable or disable caching                        |
| `log_level`     | `INFO`         | Set the logging level (`DEBUG`, `INFO`, `WARN`)  |
| `output_format` | `json`         | Format of the output (`json`, `csv`, `markdown`) |

Example configuration file (`config.yaml`):
```yaml
cache_enabled: true
log_level: INFO
output_format: json
```

### VS Code Extension Configuration

The `pytk-vscode` extension can be configured through the VS Code settings. Configuration options include:

| Option                | Default Value | Description                                      |
|-----------------------|----------------|--------------------------------------------------|
| `pytk.enable`         | `true`         | Enable or disable the extension                  |
| `pytk.logLevel`       | `info`         | Set the logging level (`debug`, `info`, `warn`)  |
| `pytk.outputFormat`   | `json`         | Format of the output (`json`, `csv`, `markdown`) |

Example settings (`settings.json`):
```json
{
    "pytk.enable": true,
    "pytk.logLevel": "info",
    "pytk.outputFormat": "json"
}
```

> **Sources:** `src/pytk/config.py` · `vscode-extension/src/extension.ts`

## Verification

After installation, you can verify that the tools are correctly installed and configured.

### Verify `pytk-cli`

1. **Check Installation**
   ```bash
   pytk --version
   ```

2. **Run a Sample Command**
   ```bash
   pytk doctor
   ```

### Verify `pytk-vscode`

1. **Check Installation**
   Open VS Code and navigate to the Extensions view. Ensure that `pytk-vscode` is listed and enabled.

2. **Run a Sample Command**
   Open the Command Palette (`Ctrl+Shift+P`), type `pytk: Doctor`, and run the command.

> **Sources:** `src/pytk/cli.py` · `vscode-extension/src/extension.ts`

---

By following these instructions, you should be able to successfully install and configure both `pytk-cli` and `pytk-vscode`. If you encounter any issues, refer to the respective documentation or seek support from the community.