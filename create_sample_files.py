#!/usr/bin/env python3
"""Create harmless sample files for the AI-Assisted Automated File Organization System."""

from pathlib import Path
import zipfile

SAMPLE_DIR = Path(__file__).resolve().parent / "sample_files"

FILES = {
    # Documents
    "resume.pdf": "%PDF-1.4\n% sample resume placeholder\n%%EOF\n",
    "assignment.txt": "College Assignment\nTopic: AI and Automation\n\nContent goes here.\n",
    "report.docx": "This is a placeholder DOCX file (sample).\n",
    "presentation.pptx": "This is a placeholder PPTX file (sample).\n",
    "contract.pdf": "%PDF-1.4\n% contract placeholder\n%%EOF\n",
    "notes.txt": "Meeting notes placeholder.\n",
    "letter.docx": "This is a placeholder DOCX letter (sample).\n",
    "slides.pptx": "This is a placeholder PPTX slides (sample).\n",
    "memo.txt": "Internal memo placeholder.\n",
    # Images
    "vacation.jpg": "This is a placeholder JPG image file (sample).\n",
    "diagram.png": "This is a placeholder PNG image file (sample).\n",
    "photo.jpeg": "This is a placeholder JPEG image file (sample).\n",
    "sunset.jpg": "This is a placeholder JPG sunset (sample).\n",
    "chart.png": "This is a placeholder PNG chart (sample).\n",
    "selfie.jpeg": "This is a placeholder JPEG selfie (sample).\n",
    "logo.gif": "This is a placeholder GIF logo (sample).\n",
    "banner.webp": "This is a placeholder WebP banner (sample).\n",
    # Spreadsheets
    "grades.csv": "Name,Score,Grade\nAlice,85,A\nBob,78,B\n",
    "budget.xlsx": "This is a placeholder XLSX file (sample).\n",
    "sales.csv": "Product,Revenue\nWidget,1000\nGadget,2500\n",
    "inventory.xlsx": "This is a placeholder XLSX inventory (sample).\n",
    "expenses.xls": "This is a placeholder XLS expenses (sample).\n",
    "data.ods": "This is a placeholder ODS spreadsheet (sample).\n",
    "report.csv": "Month,Value\nJan,100\nFeb,200\n",
    # Archives
    "backup.zip": None,  # real zip created below
    "notes.rar": "This is a placeholder RAR archive file (sample).\n",
    "archive.7z": "This is a placeholder 7Z archive file (sample).\n",
    "docs.zip": None,
    "photos.rar": "This is a placeholder RAR photos (sample).\n",
    "backup2.7z": "This is a placeholder 7Z backup (sample).\n",
    "source.tar": "This is a placeholder TAR archive (sample).\n",
    "logs.gz": "This is a placeholder GZ archive (sample).\n",
    # Other / misc
    "readme.txt": "Read me first.\n",
    "script.py": "print('Hello from sample script')\n",
    "data.json": '{"key": "value"}\n',
    "config.yaml": "key: value\n",
    "readme.md": "# Readme\nContent here.\n",
    "app.js": "console.log('sample');\n",
    "style.css": "body { color: black; }\n",
    "database.sql": "SELECT * FROM users;\n",
}


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for name, content in FILES.items():
        path = SAMPLE_DIR / name
        if content is None:
            # Create a real (valid) zip archive.
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("placeholder.txt", "sample zip contents\n")
        else:
            path.write_text(content, encoding="utf-8")
        print(f"Created {path}")
        count += 1
    print(f"\nCreated {count} sample files in {SAMPLE_DIR}")


if __name__ == "__main__":
    main()
