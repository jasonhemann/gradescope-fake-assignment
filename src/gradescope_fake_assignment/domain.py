from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

type RosterFormat = Literal["canvas", "banner"]


@dataclass(frozen=True, slots=True)
class Student:
    roster_id: str
    display_name: str


type Roster = tuple[Student, ...]


@dataclass(frozen=True, slots=True)
class CliArgs:
    assignment_name: str
    csv_path: Path
    roster_format: RosterFormat
    output_dir: Path


@dataclass(frozen=True, slots=True)
class PageSpec:
    assignment_name: str
    student_name: str | None = None


@dataclass(frozen=True, slots=True)
class RenderedDocuments:
    template_pdf: bytes
    submissions_pdf: bytes


@dataclass(frozen=True, slots=True)
class GeneratedFiles:
    template_pdf: Path
    submissions_pdf: Path
