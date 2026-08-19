from io import BytesIO
from pathlib import Path

import pytest
from pypdf import PdfReader

from gradescope_fake_assignment.__main__ import main, parse_arguments, run
from gradescope_fake_assignment.domain import CliArgs, Student
from gradescope_fake_assignment.pdf import render_documents
from gradescope_fake_assignment.roster import CsvTable, load_roster, parse_roster

TEST_RESOURCES = Path(__file__).parent / "resources"


def test_parse_arguments_defaults_to_canvas() -> None:
    args = parse_arguments(["Assignment 1", str(TEST_RESOURCES / "test-roster.csv")])

    assert args.roster_format == "canvas"


def test_load_roster_supports_canvas_gradebook_exports() -> None:
    students = load_roster(TEST_RESOURCES / "test-roster.csv", "canvas")

    assert students == (
        Student(roster_id="101", display_name="Tommy Thompson"),
        Student(roster_id="102", display_name="Timmy Thompson"),
    )


def test_load_roster_supports_banner_exports() -> None:
    students = load_roster(TEST_RESOURCES / "test-roster-banner.csv", "banner")

    assert students == (
        Student(roster_id="12345678", display_name="Tommy Thompson"),
        Student(roster_id="12345679", display_name="Timmy Thompson"),
    )


def test_load_roster_preserves_leading_zero_ids(tmp_path: Path) -> None:
    roster_path = tmp_path / "banner.csv"
    roster_path.write_text(
        'Full Name,Student ID\n"Doe, Jane",001234\n', encoding="utf-8"
    )

    students = load_roster(roster_path, "banner")

    assert students == (Student(roster_id="001234", display_name="Jane Doe"),)


def test_parse_canvas_roster_filters_nonstudents_and_preserves_order() -> None:
    table = CsvTable(
        columns=("Student", "ID"),
        rows=(
            (" Points Possible ", "ignored"),
            ("Already Ordered", "001"),
            ("Doe, Jane", "002"),
            ("Missing Identifier", ""),
            ("", "003"),
            ("Doe, Jane", "004"),
        ),
    )

    students = parse_roster(table, "canvas")

    assert students == (
        Student(roster_id="001", display_name="Already Ordered"),
        Student(roster_id="002", display_name="Jane Doe"),
        Student(roster_id="004", display_name="Jane Doe"),
    )


def test_load_roster_canvas_requires_gradebook_columns() -> None:
    with pytest.raises(
        ValueError, match=r"Canvas CSV file is missing the required column\(s\):"
    ):
        _ = load_roster(TEST_RESOURCES / "test-roster-bad-columns.csv", "canvas")


def test_load_roster_banner_requires_grade_entry_columns() -> None:
    with pytest.raises(
        ValueError, match=r"Banner CSV file is missing the required column\(s\):"
    ):
        _ = load_roster(TEST_RESOURCES / "test-roster.csv", "banner")


def test_load_roster_rejects_excel_workbooks(tmp_path: Path) -> None:
    workbook_path = tmp_path / "roster.xlsx"
    workbook_path.write_text("not an actual workbook", encoding="utf-8")

    with pytest.raises(ValueError, match="Roster input must be a CSV file"):
        _ = load_roster(workbook_path, "banner")


def _page_text(pdf_bytes: bytes) -> tuple[tuple[str, ...], ...]:
    reader = PdfReader(BytesIO(pdf_bytes))
    return tuple(
        tuple(line for line in (page.extract_text() or "").splitlines() if line)
        for page in reader.pages
    )


def test_render_documents_is_deterministic_and_preserves_page_order() -> None:
    students = (
        Student(roster_id="101", display_name="Tommy Thompson"),
        Student(roster_id="102", display_name="Timmy Thompson"),
    )

    documents = render_documents("Assignment 1", students)

    assert documents == render_documents("Assignment 1", students)
    assert _page_text(documents.template_pdf) == (
        ("Assignment: Assignment 1", "Student:"),
    )
    assert _page_text(documents.submissions_pdf) == (
        ("Assignment: Assignment 1", "Student:", "Tommy Thompson"),
        ("Assignment: Assignment 1", "Student:", "Timmy Thompson"),
    )


def test_run_returns_generated_files_without_printing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_dir = tmp_path / "nested" / "output"
    args = CliArgs(
        assignment_name="Assignment 1",
        csv_path=TEST_RESOURCES / "test-roster-banner.csv",
        roster_format="banner",
        output_dir=output_dir,
    )

    generated_files = run(args)

    assert generated_files.template_pdf == output_dir / "template.pdf"
    assert generated_files.submissions_pdf == output_dir / "submissions.pdf"
    assert capsys.readouterr() == ("", "")


def test_main_creates_only_final_outputs_for_banner_roster(tmp_path: Path) -> None:
    output_dir = tmp_path / "nested" / "output"
    exit_code = main(
        [
            "Assignment 1",
            str(TEST_RESOURCES / "test-roster-banner.csv"),
            "--format",
            "banner",
            "--output_dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert {path.name for path in output_dir.iterdir()} == {
        "template.pdf",
        "submissions.pdf",
    }


def test_invalid_roster_does_not_create_output_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output_dir = tmp_path / "nested" / "output"

    exit_code = main(
        [
            "Assignment 1",
            str(TEST_RESOURCES / "test-roster-bad-columns.csv"),
            "--format",
            "canvas",
            "--output_dir",
            str(output_dir),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert not output_dir.exists()
    assert "Canvas CSV file is missing the required column(s)" in captured.err
