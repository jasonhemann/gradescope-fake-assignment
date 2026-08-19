from pathlib import Path

import pytest

from gradescope_fake_assignment.__main__ import main, parse_arguments
from gradescope_fake_assignment.domain import Student
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


def test_main_creates_outputs_for_banner_roster(tmp_path: Path) -> None:
    exit_code = main(
        [
            "Assignment 1",
            str(TEST_RESOURCES / "test-roster-banner.csv"),
            "--format",
            "banner",
            "--output_dir",
            str(tmp_path),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "template.pdf").is_file()
    assert (tmp_path / "submissions.pdf").is_file()
