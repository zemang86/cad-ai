#!/usr/bin/env python3
"""Extract UBBL PDF into structured text files for knowledge base creation.

Usage:
    .venv/bin/python scripts/extract_ubbl.py "sample/UKBS 1984 1C.pdf" --output-dir /tmp/ubbl-extract

This script extracts raw text from the UBBL PDF, split by Part and By-law,
to assist in creating curated Markdown knowledge base files. The output is
raw extracted text — final knowledge base files should be manually curated
with proper formatting (bold thresholds, citation blocks, section headers).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def extract_full_text(pdf_path: str) -> str:
    """Extract all text from the PDF."""
    import fitz  # pymupdf

    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    return "\n".join(pages)


def find_part_boundaries(lines: list[str]) -> list[tuple[int, str]]:
    """Find line indices where main UBBL Parts begin (body text, not ToC)."""
    boundaries = []
    # The body content Parts appear after the ToC (roughly after line 700)
    # They follow pattern: "PART [roman]" on its own line, then title on next line
    for i, line in enumerate(lines):
        stripped = line.strip()
        if i < 700:
            continue
        # Match "PART I", "PART IA", "PART II", etc. as standalone
        if re.match(r"^PART\s+[IVX]+[A-Z]?$", stripped):
            # Get the title from next non-empty line
            title = ""
            for j in range(i + 1, min(i + 5, len(lines))):
                candidate = lines[j].strip()
                if candidate and not candidate.startswith("["):
                    title = candidate
                    break
            boundaries.append((i, f"{stripped} — {title}"))
    return boundaries


def find_schedule_boundaries(lines: list[str]) -> list[tuple[int, str]]:
    """Find line indices where Schedules begin."""
    ordinals = [
        "FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH",
        "SIXTH", "SEVENTH", "EIGHT", "NINTH", "TENTH", "ELEVENTH",
    ]
    boundaries = []
    for i, line in enumerate(lines):
        if i < 5000:
            continue
        stripped = line.strip()
        for ordinal in ordinals:
            if f"{ordinal} SCHEDULE" in stripped and "BAHAGIAN" not in lines[max(0, i - 5):i + 1]:
                # Skip if this is in the Malay translation section (after ~line 16000)
                if i > 16000:
                    continue
                # Get subtitle
                title = ""
                for j in range(i + 1, min(i + 5, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and not candidate.startswith("[") and candidate != stripped:
                        title = candidate
                        break
                boundaries.append((i, f"{ordinal} SCHEDULE — {title}"))
                break
    return boundaries


def extract_section(lines: list[str], start: int, end: int) -> str:
    """Extract text between two line indices."""
    return "\n".join(lines[start:end])


def split_by_bylaws(text: str) -> list[tuple[str, str]]:
    """Split a Part's text into individual by-laws."""
    # Pattern: "By-law 123." or "By-law 123A."
    pattern = r"^(By-law\s+\d+[A-Z]?\.)"
    bylaws = []
    current_header = "Preamble"
    current_text = []

    for line in text.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            if current_text:
                bylaws.append((current_header, "\n".join(current_text)))
            current_header = match.group(1)
            current_text = [line]
        else:
            current_text.append(line)

    if current_text:
        bylaws.append((current_header, "\n".join(current_text)))

    return bylaws


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract UBBL PDF into text files")
    parser.add_argument("pdf_path", help="Path to the UBBL PDF file")
    parser.add_argument(
        "--output-dir",
        default="/tmp/ubbl-extract",
        help="Output directory for extracted text files",
    )
    args = parser.parse_args()

    pdf_path = args.pdf_path
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting text from: {pdf_path}")
    full_text = extract_full_text(pdf_path)
    lines = full_text.split("\n")
    print(f"Total lines: {len(lines)}")

    # Save full text
    (output_dir / "full_text.txt").write_text(full_text, encoding="utf-8")
    print(f"Full text saved to: {output_dir / 'full_text.txt'}")

    # Find and extract Parts
    parts = find_part_boundaries(lines)
    print(f"\nFound {len(parts)} Parts:")
    for idx, (line_num, title) in enumerate(parts):
        # Determine end boundary
        if idx + 1 < len(parts):
            end = parts[idx + 1][0]
        else:
            end = len(lines)

        section_text = extract_section(lines, line_num, end)
        filename = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
        filepath = output_dir / f"part_{filename}.txt"
        filepath.write_text(section_text, encoding="utf-8")
        print(f"  {title} (lines {line_num}-{end}) -> {filepath.name}")

        # Also split by by-laws
        bylaws = split_by_bylaws(section_text)
        if len(bylaws) > 1:
            bylaws_dir = output_dir / f"part_{filename}_bylaws"
            bylaws_dir.mkdir(exist_ok=True)
            for header, content in bylaws:
                bylaw_filename = re.sub(r"[^a-zA-Z0-9]+", "_", header).strip("_").lower()
                (bylaws_dir / f"{bylaw_filename}.txt").write_text(
                    content, encoding="utf-8"
                )

    # Find and extract Schedules
    schedules = find_schedule_boundaries(lines)
    print(f"\nFound {len(schedules)} Schedules:")
    for idx, (line_num, title) in enumerate(schedules):
        if idx + 1 < len(schedules):
            end = schedules[idx + 1][0]
        else:
            # End at the Malay translation section or end of document
            end = min(line_num + 2000, len(lines))
            for j in range(line_num + 10, len(lines)):
                if "MALAYSIA" in lines[j] and "PERUNDANGAN" in lines[j + 2]:
                    end = j
                    break

        section_text = extract_section(lines, line_num, end)
        filename = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_").lower()
        filepath = output_dir / f"schedule_{filename}.txt"
        filepath.write_text(section_text, encoding="utf-8")
        print(f"  {title} (lines {line_num}-{end}) -> {filepath.name}")

    print(f"\nExtraction complete. Files saved to: {output_dir}")


if __name__ == "__main__":
    main()
