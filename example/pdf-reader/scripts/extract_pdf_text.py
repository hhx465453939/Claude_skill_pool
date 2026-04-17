#!/usr/bin/env python3
"""Extract text from a text-based PDF into Markdown using pdfplumber."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract text from a local PDF into Markdown with pdfplumber."
    )
    parser.add_argument("input_pdf", help="Path to the source PDF file")
    parser.add_argument(
        "-o",
        "--output",
        help="Output Markdown path. Defaults to <input>.md beside the PDF.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write Markdown to stdout instead of a file.",
    )
    parser.add_argument(
        "--first-page",
        type=int,
        default=1,
        help="First page to extract (1-based, default: 1).",
    )
    parser.add_argument(
        "--last-page",
        type=int,
        help="Last page to extract (1-based, default: last page in the PDF).",
    )
    return parser


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    lines = [line.rstrip() for line in text.split("\n")]
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def default_output_path(input_pdf: Path) -> Path:
    return input_pdf.with_suffix(".md")


def render_markdown(input_pdf: Path, first_page: int, last_page: int) -> str:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pdfplumber is not installed. Run this script with "
            "`uv run --with pdfplumber python3 ...` or install pdfplumber first."
        ) from exc

    with pdfplumber.open(input_pdf) as pdf:
        total_pages = len(pdf.pages)
        if total_pages == 0:
            raise RuntimeError("The PDF has no pages.")

        if first_page < 1:
            raise RuntimeError("--first-page must be >= 1.")

        effective_last_page = last_page or total_pages
        if effective_last_page < first_page:
            raise RuntimeError("--last-page must be >= --first-page.")

        if first_page > total_pages:
            raise RuntimeError(
                f"--first-page {first_page} exceeds total pages {total_pages}."
            )

        effective_last_page = min(effective_last_page, total_pages)

        sections = [
            f"# {input_pdf.name}",
            "",
            f"- Source: `{input_pdf}`",
            f"- Pages extracted: {first_page}-{effective_last_page} / {total_pages}",
            f"- Extractor: `pdfplumber`",
            "",
        ]

        total_chars = 0

        for page_number in range(first_page, effective_last_page + 1):
            raw_text = pdf.pages[page_number - 1].extract_text() or ""
            page_text = normalize_text(raw_text)
            sections.append(f"## Page {page_number}")
            sections.append("")

            if page_text:
                sections.append(page_text)
                total_chars += len(page_text)
            else:
                sections.append("> [No extractable text found on this page]")

            sections.append("")

        if total_chars == 0:
            raise RuntimeError(
                "No extractable text was found. This PDF is likely scanned, image-based, "
                "or otherwise missing a usable text layer."
            )

        return "\n".join(sections).rstrip() + "\n"


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_pdf = Path(args.input_pdf).expanduser().resolve()
    if not input_pdf.exists():
        print(f"Input PDF not found: {input_pdf}", file=sys.stderr)
        return 1
    if input_pdf.suffix.lower() != ".pdf":
        print(f"Input is not a PDF file: {input_pdf}", file=sys.stderr)
        return 1

    try:
        markdown = render_markdown(
            input_pdf=input_pdf,
            first_page=args.first_page,
            last_page=args.last_page,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.stdout:
        sys.stdout.write(markdown)
        return 0

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_output_path(input_pdf)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
