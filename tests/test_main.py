from pathlib import Path

import pytest

from gradescope_fake_assignment.__main__ import load_roster, main, parse_arguments

TEST_RESOURCES = Path(__file__).parent / "resources"


def test_parse_arguments_defaults_to_canvas() -> None:
    args = parse_arguments(["Assignment 1", str(TEST_RESOURCES / "test-roster.csv")])

    assert args.roster_format == "canvas"


def test_load_roster_supports_canvas_gradebook_exports() -> None:
    student_names = load_roster(TEST_RESOURCES / "test-roster.csv", "canvas")

    assert student_names == ["Tommy Thompson", "Timmy Thompson"]


def test_load_roster_supports_banner_exports() -> None:
    student_names = load_roster(TEST_RESOURCES / "test-roster-banner.csv", "banner")

    assert student_names == ["Tommy Thompson", "Timmy Thompson"]


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
