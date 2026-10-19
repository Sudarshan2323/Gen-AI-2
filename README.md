# AI-Assisted Automated File Organization System

A college practical project that automatically organizes files into suitable
folders. Optionally uses **NVIDIA Nemotron 3.5 Super** (via the NVIDIA NIM
API) to suggest folder categories, with full fallback to extension-based
rules when the API is unavailable.

## Project structure

```
main.py                 # Application entry point
create_sample_files.py  # Script that generates harmless sample files
requirements.txt        # Python dependencies (stdlib only)
.env.example            # API key template (copy to .env and fill in)
.gitignore              # Git ignore rules
README.md               # This file
sample_files/           # Input files to organize (created by create_sample_files.py)
organized_files/        # Output organized folders (created at runtime)
reports/                # JSON/CSV organization reports (created at runtime)
```

## Features

* Automatic file detection by filename and extension.
* Categories: Documents, Images, Spreadsheets, Archives, Other.
* Optional AI-assisted category suggestions from NVIDIA Nemotron 3.5 Super.
* AI suggestions treated as untrusted input; validated against allowed categories.
* Preview / dry-run mode lists every proposed move before changes.
* Explicit user confirmation required before moving files.
* Never overwrites files; duplicate names are renamed safely (`file_1.ext`).
* All operations restricted to directories inside the project root.
* Falls back to extension-based rules if the NVIDIA API is unavailable.
* Generates JSON and CSV organization reports.
* Logging, exception handling, and clear console messages.

## Setup (Windows PowerShell)

### 1. Create the project folder and files

Place all the source files above in one folder, e.g. `C:\Gen-AI\AI-Agent Q4\`.

### 2. Create a virtual environment (recommended)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

No external packages are required (standard library only). Optional:

```powershell
pip install python-dotenv
```

### 4. Configure the NVIDIA API key (optional)

Copy the example env file and add your NVIDIA NIM API key:

```powershell
Copy-Item .env.example .env
# Edit .env and paste your NVIDIA_API_KEY
```

If you do not set `NVIDIA_API_KEY`, the app runs in fallback mode using
extension-based rules and reports this clearly.

### 5. Create the sample files

```powershell
python create_sample_files.py
```

This creates 15 harmless sample files (PDF, TXT, DOCX, PPTX, JPG, PNG, JPEG,
CSV, XLSX, ZIP, RAR, 7Z, PY, JSON) in `sample_files/`.

## Execution

### Dry-run (preview only — recommended first)

```powershell
python main.py --dry-run
```

You will see every proposed file movement. No files are changed.

### Apply changes (with confirmation)

```powershell
python main.py --live
```

The dry-run preview is shown first, then you are asked to confirm before any
files are moved.

### Skip confirmation

```powershell
python main.py --live --yes
```

### Disable AI (force extension-based rules)

```powershell
python main.py --live --no-ai
```

### Verbose logging

```powershell
python main.py --live --verbose
```

## What gets created

After a live run, `organized_files/` contains subfolders:

```
organized_files/
  Documents/
  Images/
  Spreadsheets/
  Archives/
  Other/
```

`reports/` contains `organization_report_<timestamp>.json` and
`.csv` with columns:

`timestamp, original_filename, destination_category,
 classification_source, used_ai, destination_path, action, error`

## Test scenarios covered

| Scenario | How to verify |
|---|---|
| Classification by extension | Run with `--no-ai` or no API key; check report `classification_source` |
| AI suggestion | Set `NVIDIA_API_KEY`; check `used_ai = true` |
| Preview mode | `python main.py --dry-run` shows moves but changes nothing |
| Confirmation | `--live` prompts before moving |
| Duplicate filenames | Run twice; second run renames `file_1.ext` |
| API failure / fallback | Unset `NVIDIA_API_KEY`; app reports fallback mode |
| Folder restriction | All paths stay under the project root |

## Example report row

```json
{
  "timestamp": "2026-10-19T10:00:00",
  "original_filename": "resume.pdf",
  "destination_category": "Documents",
  "classification_source": "Extension-based rule",
  "used_ai": false,
  "destination_path": "organized_files/Documents/resume.pdf",
  "action": "moved",
  "error": ""
}
```
