#!/usr/bin/env python3
"""
AI-Assisted Automated File Organization System
==============================================

Automatically organizes files into suitable folders. Optionally uses
NVIDIA Nemotron 3.5 Super (via the NVIDIA NIM API) to suggest folder
categories, with full fallback to extension-based rules when the API is
unavailable.

Standard library only (plus optional python-dotenv).

Safety guarantees:
  * AI suggestions are treated as untrusted and validated against the
    allowed category set before use.
  * A preview/dry-run lists every proposed movement before anything changes.
  * Explicit user confirmation is required before moving files.
  * Files are never overwritten; duplicates are renamed safely.
  * All operations are restricted to directories inside the project root.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = PROJECT_ROOT / "sample_files"
DEST_DIR = PROJECT_ROOT / "organized_files"
REPORTS_DIR = PROJECT_ROOT / "reports"

ALLOWED_CATEGORIES = {"Documents", "Images", "Spreadsheets", "Archives", "Other"}

EXTENSION_MAP = {
    ".pdf": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".doc": "Documents",
    ".rtf": "Documents",
    ".pptx": "Documents",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".webp": "Images",
    ".csv": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".xls": "Spreadsheets",
    ".ods": "Spreadsheets",
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
}

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"


def setup_logging(verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("file_organizer")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    return logger


# ---------------------------------------------------------------------------
# AI category suggester (NVIDIA Nemotron 3.5 Super via NIM API)
# ---------------------------------------------------------------------------

class AICategorySuggester:
    """Suggests a folder category for a filename using the NVIDIA NIM API.

    All suggestions are treated as untrusted and validated against the
    allowed category set before being used.
    """

    def __init__(
        self,
        api_key: Optional[str],
        api_base: str,
        model: str,
        logger: logging.Logger,
    ):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.logger = logger

    def suggest(self, filename: str) -> Optional[str]:
        if not self.api_key:
            self.logger.debug("No NVIDIA API key configured; cannot call AI.")
            return None
        try:
            category = self._call_api(filename)
        except Exception as exc:  # noqa: BLE001 - network/API failures expected
            self.logger.warning("AI suggestion failed for %s: %s", filename, exc)
            return None
        if not category:
            return None
        # Treat AI output as untrusted: validate against allowed categories.
        normalized = category.strip()
        for allowed in ALLOWED_CATEGORIES:
            if normalized.lower() == allowed.lower():
                return allowed
        self.logger.debug(
            "AI suggested '%s' which is not an allowed category; ignoring.", category
        )
        return None

    def _call_api(self, filename: str) -> Optional[str]:
        prompt = (
            "You are a file-organization assistant. Given only a filename, "
            "suggest the single best folder category from this exact list: "
            "Documents, Images, Spreadsheets, Archives, Other. "
            "Reply with exactly one category name and nothing else.\n\n"
            f"Filename: {filename}"
        )
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 20,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            f"{self.api_base}/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
        result = json.loads(body)
        content = result["choices"][0]["message"]["content"]
        return content.strip()


# ---------------------------------------------------------------------------
# Core organizer
# ---------------------------------------------------------------------------

class FileOrganizer:
    def __init__(
        self,
        sample_dir: Path = SAMPLE_DIR,
        dest_dir: Path = DEST_DIR,
        reports_dir: Path = REPORTS_DIR,
        dry_run: bool = True,
        use_ai: bool = True,
        verbose: bool = False,
    ):
        self.sample_dir = sample_dir.resolve()
        self.dest_dir = dest_dir.resolve()
        self.reports_dir = reports_dir.resolve()
        self.dry_run = dry_run
        self.use_ai = use_ai
        self.logger = setup_logging(verbose)
        self.report_rows = []
        self.errors = []

        # Safety: restrict operations to directories inside the project root.
        self._validate_directory(self.sample_dir, "sample directory")
        self._validate_directory(self.dest_dir, "destination directory")

        ai_key = os.environ.get("NVIDIA_API_KEY")
        ai_base = os.environ.get("NVIDIA_API_BASE", "https://integrate.api.nvidia.com")
        ai_model = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3.5-super")
        self.ai = (
            AICategorySuggester(ai_key, ai_base, ai_model, self.logger) if use_ai else None
        )

    @staticmethod
    def _validate_directory(path: Path, label: str) -> None:
        if not path.is_relative_to(PROJECT_ROOT):
            raise ValueError(f"{label} must be inside the project root: {path}")

    def classify_extension(self, path: Path) -> str:
        return EXTENSION_MAP.get(path.suffix.lower(), "Other")

    def classify(self, path: Path) -> tuple[str, str, bool]:
        """Return (category, source, used_ai)."""
        if self.ai is not None:
            ai_category = self.ai.suggest(path.name)
            if ai_category is not None:
                return ai_category, "AI (Nemotron 3.5 Super)", True
        return self.classify_extension(path), "Extension-based rule", False

    def destination_path(self, category: str, src: Path) -> Path:
        target_dir = self.dest_dir / category
        target = target_dir / src.name
        if not target.exists():
            return target
        # Handle duplicates safely: never overwrite.
        stem = src.stem
        suffix = src.suffix
        counter = 1
        while True:
            candidate = target_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def organize(self) -> None:
        if not self.sample_dir.exists():
            self.logger.error("Sample directory does not exist: %s", self.sample_dir)
            return

        files = sorted(
            p for p in self.sample_dir.iterdir() if p.is_file() and not p.name.startswith(".")
        )
        if not files:
            self.logger.warning("No files found in %s", self.sample_dir)
            return

        mode = "DRY-RUN" if self.dry_run else "LIVE"
        self.logger.info("Starting organization (%s mode) on %d file(s)", mode, len(files))

        if self.dry_run:
            print("\n=== PREVIEW: proposed file movements ===\n")

        for src in files:
            category, source, used_ai = self.classify(src)
            dest = self.destination_path(category, src)
            action = "would_move" if self.dry_run else "moved"
            error = ""

            if self.dry_run:
                rel_src = src.relative_to(PROJECT_ROOT)
                rel_dest = dest.relative_to(PROJECT_ROOT)
                print(f"  {rel_src}  -->  {rel_dest}  [{category}]")
            else:
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dest))
                    self.logger.info("Moved %s -> %s (%s)", src.name, dest, category)
                except Exception as exc:  # noqa: BLE001
                    error = str(exc)
                    self.logger.error("Failed to move %s: %s", src.name, exc)
                    action = "error"

            self.report_rows.append(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "original_filename": src.name,
                    "destination_category": category,
                    "classification_source": source,
                    "used_ai": used_ai,
                    "destination_path": str(dest.relative_to(PROJECT_ROOT)),
                    "action": action,
                    "error": error,
                }
            )

        if not self.dry_run:
            self._write_report()
            self.logger.info("Organization complete. Report written to %s", self.reports_dir)
        else:
            print("\n=== END OF PREVIEW ===")
            print(f"Total files previewed: {len(files)}")
            print("\nNo files were moved. Run without --dry-run to apply changes.")

    def confirm(self) -> bool:
        prompt = "\nProceed with moving these files? (yes/no): "
        try:
            answer = input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled by user.")
            return False
        return answer in {"y", "yes"}

    def _write_report(self) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self.reports_dir / f"organization_report_{timestamp}.json"
        csv_path = self.reports_dir / f"organization_report_{timestamp}.csv"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.report_rows, f, indent=2)

        fieldnames = [
            "timestamp",
            "original_filename",
            "destination_category",
            "classification_source",
            "used_ai",
            "destination_path",
            "action",
            "error",
        ]
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.report_rows)

        self.logger.info("Reports: %s", json_path)
        self.logger.info("Reports: %s", csv_path)


# ---------------------------------------------------------------------------
# urllib import (placed here to keep module-level imports tidy)
# ---------------------------------------------------------------------------

import urllib.request as urllib_request  # noqa: E402


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> dict:
    args = {"dry_run": True, "use_ai": True, "verbose": False, "confirm": True}
    i = 0
    while i < len(argv):
        token = argv[i]
        if token in ("--dry-run", "-n"):
            args["dry_run"] = True
        elif token == "--live":
            args["dry_run"] = False
        elif token == "--no-ai":
            args["use_ai"] = False
        elif token in ("--verbose", "-v"):
            args["verbose"] = True
        elif token in ("--yes", "-y"):
            args["confirm"] = False
        elif token in ("--help", "-h"):
            print(__doc__)
            print(
                "\nUsage: python main.py [--live] [--dry-run] [--no-ai] [--yes] [--verbose]"
            )
            sys.exit(0)
        else:
            print(f"Unknown argument: {token}")
            sys.exit(2)
        i += 1
    return args


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = parse_args(argv)

    if args["use_ai"] and not os.environ.get("NVIDIA_API_KEY"):
        print("NOTE: NVIDIA_API_KEY not set. Falling back to extension-based rules.")

    organizer = FileOrganizer(
        dry_run=args["dry_run"],
        use_ai=args["use_ai"],
        verbose=args["verbose"],
    )

    if args["dry_run"]:
        organizer.organize()
        if args["confirm"]:
            if not organizer.confirm():
                return 0
            organizer.report_rows = []
            organizer.dry_run = False
            organizer.organize()
        else:
            print("Skipping confirmation (--yes). Running live...")
            organizer.report_rows = []
            organizer.dry_run = False
            organizer.organize()
    else:
        if args["confirm"] and not organizer.confirm():
            return 0
        organizer.organize()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
