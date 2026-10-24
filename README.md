# Account Intelligence

A lightweight application for prioritizing B2B SaaS customer accounts and generating actionable account insights.

Built with React, TypeScript, and FastAPI.

**Current status:** The application is functional end-to-end, but account scoring and insights currently use mock logic.

## Prerequisites

- Python 3.12
- Node.js 24 (includes npm)
- Git
- uv (Python package manager)

### Windows

Install Python and Node.js using PowerShell:

```powershell
winget install --id Python.Python.3.12 --exact
winget install --id OpenJS.NodeJS.LTS --exact
```

Close and reopen your terminal after installation.

Install uv:

```powershell
py -3.12 -m pip install uv
```

### macOS

Install Python 3.12 and Node.js 24 using their official installers:

- [Python](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/en/download)

Install uv:

```bash
python3 -m pip install uv
```

## Installation

Clone the repository:

```bash
git clone https://github.com/marencjusz/account-orbit-insight-compass.git
cd account-orbit-insight-compass
```

Install frontend and backend dependencies:

```bash
npm ci
uv sync
```

## Running the application

From the repository root, run:

```bash
uv run python run.py
```

Open **http://127.0.0.1:5173** in your browser.

The launcher starts both services:

- Frontend: `http://127.0.0.1:5173`
- FastAPI backend: `http://127.0.0.1:8000`
- API documentation: `http://127.0.0.1:8000/docs`

Press `Ctrl+C` in the terminal to stop the application.

## Platform compatibility

The application has been developed and tested on **Windows**.

macOS installation and execution instructions are provided, but have not been independently tested. No Docker or cloud deployment is required.