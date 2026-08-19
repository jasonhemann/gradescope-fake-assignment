from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from gradescope_fake_assignment.domain import Roster, RosterFormat, Student

CANVAS_NAME_COLUMN = "Student"
CANVAS_ID_COLUMN = "ID"
BANNER_NAME_COLUMN = "Full Name"
BANNER_ID_COLUMN = "Student ID"


@dataclass(frozen=True, slots=True)
class CsvTable:
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class RosterColumns:
    name: int
    roster_id: int


def read_csv(csv_path: Path) -> CsvTable:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file '{csv_path}' does not exist.")
    if csv_path.suffix.casefold() != ".csv":
        message = (
            "Roster input must be a CSV file. "
            "Convert Excel workbooks to CSV before running this program."
        )
        raise ValueError(message)

    with csv_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        columns = tuple(next(reader, ()))
        rows = tuple(tuple(row) for row in reader if any(cell.strip() for cell in row))

    return CsvTable(columns=columns, rows=rows)


def _roster_columns(
    table: CsvTable,
    roster_format: RosterFormat,
    name_column: str,
    id_column: str,
) -> RosterColumns:
    required_columns = (name_column, id_column)
    missing_columns = tuple(
        column for column in required_columns if column not in table.columns
    )
    if missing_columns:
        missing = ", ".join(missing_columns)
        message = (
            f"{roster_format.title()} CSV file is missing the required "
            f"column(s): {missing}"
        )
        raise ValueError(message)

    return RosterColumns(
        name=table.columns.index(name_column),
        roster_id=table.columns.index(id_column),
    )


def _cell(row: tuple[str, ...], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


def _format_last_first_name(raw_name: str) -> str:
    stripped_name = raw_name.strip()
    last_name, separator, first_name = stripped_name.partition(",")
    if not separator:
        return stripped_name

    ordered_parts = (first_name.strip(), last_name.strip())
    return " ".join(part for part in ordered_parts if part)


def _students_from_table(
    table: CsvTable,
    roster_format: RosterFormat,
    name_column: str,
    id_column: str,
    *,
    skip_points_possible: bool = False,
) -> Roster:
    columns = _roster_columns(table, roster_format, name_column, id_column)
    names_and_ids = (
        (_cell(row, columns.name), _cell(row, columns.roster_id)) for row in table.rows
    )
    return tuple(
        Student(
            roster_id=roster_id,
            display_name=_format_last_first_name(raw_name),
        )
        for raw_name, roster_id in names_and_ids
        if raw_name
        and roster_id
        and not (skip_points_possible and raw_name.casefold() == "points possible")
    )


def parse_roster(table: CsvTable, roster_format: RosterFormat) -> Roster:
    if roster_format == "canvas":
        return _students_from_table(
            table,
            roster_format,
            CANVAS_NAME_COLUMN,
            CANVAS_ID_COLUMN,
            skip_points_possible=True,
        )
    return _students_from_table(
        table,
        roster_format,
        BANNER_NAME_COLUMN,
        BANNER_ID_COLUMN,
    )


def load_roster(csv_path: Path, roster_format: RosterFormat) -> Roster:
    return parse_roster(read_csv(csv_path), roster_format)
