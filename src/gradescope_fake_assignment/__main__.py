from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from gradescope_fake_assignment.domain import (
    CliArgs,
    GeneratedFiles,
    RenderedDocuments,
    RosterFormat,
)
from gradescope_fake_assignment.pdf import render_documents
from gradescope_fake_assignment.roster import load_roster


def _coerce_str(value: object, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _coerce_format(value: str) -> RosterFormat:
    if value not in {"canvas", "banner"}:
        raise ValueError(f"Unsupported roster format: {value}")
    return cast(RosterFormat, value)


def parse_arguments(argv: Sequence[str] | None = None) -> CliArgs:
    parser = argparse.ArgumentParser(description="Generate Gradescope PDF submissions.")
    _ = parser.add_argument("assignment_name", type=str, help="Name of the assignment.")
    _ = parser.add_argument(
        "csv_path", type=str, help="Path to the CSV file with student roster."
    )
    _ = parser.add_argument(
        "--format",
        type=str,
        choices=["canvas", "banner"],
        default="canvas",
        help=(
            "Roster CSV format: canvas reads a Canvas gradebook export; banner "
            "reads a Banner Grade Entry workbook saved as CSV."
        ),
    )
    _ = parser.add_argument(
        "--output_dir", type=str, default=".", help="Directory to save output PDFs."
    )
    namespace = parser.parse_args(argv)
    return CliArgs(
        assignment_name=_coerce_str(getattr(namespace, "assignment_name", ""), ""),
        csv_path=Path(_coerce_str(getattr(namespace, "csv_path", ""), "")),
        roster_format=_coerce_format(
            _coerce_str(getattr(namespace, "format", "canvas"), "canvas")
        ),
        output_dir=Path(_coerce_str(getattr(namespace, "output_dir", "."), ".")),
    )


def _write_documents(documents: RenderedDocuments, output_dir: Path) -> GeneratedFiles:
    output_dir.mkdir(parents=True, exist_ok=True)
    template_pdf_path = output_dir / "template.pdf"
    submissions_pdf_path = output_dir / "submissions.pdf"
    _ = template_pdf_path.write_bytes(documents.template_pdf)
    _ = submissions_pdf_path.write_bytes(documents.submissions_pdf)
    return GeneratedFiles(
        template_pdf=template_pdf_path,
        submissions_pdf=submissions_pdf_path,
    )


def run(args: CliArgs) -> GeneratedFiles:
    students = load_roster(args.csv_path, args.roster_format)
    documents = render_documents(args.assignment_name, students)
    return _write_documents(documents, args.output_dir)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_arguments(argv)
    print("Generating Gradescope PDFs...")
    try:
        generated_files = run(args)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Template PDF created at: {generated_files.template_pdf}")
    print(f"Submissions PDF created at: {generated_files.submissions_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
