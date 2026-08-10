from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

import pandas as pd
from pandas import DataFrame
from pikepdf import Pdf
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

type RosterFormat = Literal["canvas", "banner"]
type RosterLoader = Callable[[DataFrame], list[str]]

CANVAS_NAME_COLUMN = "Student"
CANVAS_ID_COLUMN = "ID"
BANNER_NAME_COLUMN = "Full Name"
BANNER_ID_COLUMN = "Student ID"


@dataclass(slots=True)
class CliArgs:
    assignment_name: str
    csv_path: Path
    roster_format: RosterFormat
    output_dir: Path


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


def _require_columns(
    roster: DataFrame, roster_format: RosterFormat, required_columns: tuple[str, ...]
) -> None:
    missing_columns = [
        column for column in required_columns if column not in roster.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        message = f"{roster_format.title()} CSV file is missing the required column(s): {missing}"
        raise ValueError(message)


def _format_last_first_name(raw_name: str) -> str:
    stripped_name = raw_name.strip()
    last_name, separator, first_name = stripped_name.partition(",")
    if not separator:
        return stripped_name

    ordered_parts = [first_name.strip(), last_name.strip()]
    return " ".join(part for part in ordered_parts if part)


def _names_from_canvas_roster(roster: DataFrame) -> list[str]:
    _require_columns(roster, "canvas", (CANVAS_NAME_COLUMN, CANVAS_ID_COLUMN))

    raw_names = roster[CANVAS_NAME_COLUMN].fillna("").astype(str).str.strip().tolist()
    canvas_ids = roster[CANVAS_ID_COLUMN].fillna("").astype(str).str.strip().tolist()

    return [
        _format_last_first_name(name)
        for name, canvas_id in zip(raw_names, canvas_ids, strict=True)
        if name and canvas_id and name.casefold() != "points possible"
    ]


def _names_from_banner_roster(roster: DataFrame) -> list[str]:
    _require_columns(roster, "banner", (BANNER_NAME_COLUMN, BANNER_ID_COLUMN))

    raw_names = roster[BANNER_NAME_COLUMN].fillna("").astype(str).str.strip().tolist()
    student_ids = roster[BANNER_ID_COLUMN].fillna("").astype(str).str.strip().tolist()

    return [
        _format_last_first_name(name)
        for name, student_id in zip(raw_names, student_ids, strict=True)
        if name and student_id
    ]


ROSTER_LOADERS: dict[RosterFormat, RosterLoader] = {
    "canvas": _names_from_canvas_roster,
    "banner": _names_from_banner_roster,
}


def load_roster(csv_path: Path, roster_format: RosterFormat) -> list[str]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file '{csv_path}' does not exist.")
    if csv_path.suffix.casefold() != ".csv":
        message = "Roster input must be a CSV file. Convert Excel workbooks to CSV before running this program."
        raise ValueError(message)

    roster = pd.read_csv(csv_path)
    return ROSTER_LOADERS[roster_format](roster)


def create_template_pdf(assignment_name: str, output_path: Path) -> None:
    pdf_canvas = canvas.Canvas(str(output_path), pagesize=LETTER)
    pdf_canvas.drawString(100, 700, f"Assignment: {assignment_name}")
    pdf_canvas.drawString(100, 650, "Student:")
    pdf_canvas.line(150, 645, 400, 645)
    pdf_canvas.showPage()
    pdf_canvas.save()


def create_student_pdf(
    assignment_name: str, student_name: str, output_path: Path
) -> None:
    pdf_canvas = canvas.Canvas(str(output_path), pagesize=LETTER)
    pdf_canvas.drawString(100, 700, f"Assignment: {assignment_name}")
    pdf_canvas.drawString(100, 650, "Student:")
    text_width = pdf_canvas.stringWidth(student_name, "Helvetica", 12)
    pdf_canvas.drawString(150, 650, student_name)
    pdf_canvas.line(150, 645, 150 + text_width, 645)
    pdf_canvas.showPage()
    pdf_canvas.save()


def combine_pdfs(
    student_names: list[str], assignment_name: str, output_dir: Path
) -> Path:
    combined_pdf_path = output_dir / "submissions.pdf"
    temp_student_pdfs: list[Path] = []
    combined_pdf = Pdf.new()

    for idx, student_name in enumerate(student_names):
        safe_student_name = student_name.replace(" ", "_").replace("/", "_")
        student_pdf_path = output_dir / f"{safe_student_name}_{idx}_submission.pdf"
        temp_student_pdfs.append(student_pdf_path)
        create_student_pdf(assignment_name, student_name, student_pdf_path)
        with Pdf.open(student_pdf_path) as student_pdf:
            combined_pdf.pages.append(student_pdf.pages[0])

    combined_pdf.save(combined_pdf_path)

    for pdf_path in temp_student_pdfs:
        if pdf_path.exists():
            pdf_path.unlink()

    print(f"Submissions PDF created at: {combined_pdf_path}")
    return combined_pdf_path


def run(args: CliArgs) -> int:
    args.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        student_names = load_roster(args.csv_path, args.roster_format)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    template_pdf_path = args.output_dir / "template.pdf"
    create_template_pdf(args.assignment_name, template_pdf_path)
    print(f"Template PDF created at: {template_pdf_path}")
    _ = combine_pdfs(student_names, args.assignment_name, args.output_dir)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_arguments(argv)
    print("Generating Gradescope PDFs...")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
