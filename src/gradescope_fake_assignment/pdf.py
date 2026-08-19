from __future__ import annotations

from collections.abc import Sequence
from io import BytesIO

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from gradescope_fake_assignment.domain import (
    PageSpec,
    RenderedDocuments,
    Roster,
)


def _draw_page(pdf_canvas: canvas.Canvas, page: PageSpec) -> None:
    pdf_canvas.drawString(100, 700, f"Assignment: {page.assignment_name}")
    pdf_canvas.drawString(100, 650, "Student:")

    if page.student_name is None:
        pdf_canvas.line(150, 645, 400, 645)
    else:
        text_width = pdf_canvas.stringWidth(page.student_name, "Helvetica", 12)
        pdf_canvas.drawString(150, 650, page.student_name)
        pdf_canvas.line(150, 645, 150 + text_width, 645)

    pdf_canvas.showPage()


def render_pages(pages: Sequence[PageSpec]) -> bytes:
    output = BytesIO()
    pdf_canvas = canvas.Canvas(output, pagesize=LETTER, invariant=1)
    for page in pages:
        _draw_page(pdf_canvas, page)
    pdf_canvas.save()
    return output.getvalue()


def render_documents(assignment_name: str, students: Roster) -> RenderedDocuments:
    template_page = PageSpec(assignment_name=assignment_name)
    student_pages = tuple(
        PageSpec(
            assignment_name=assignment_name,
            student_name=student.display_name,
        )
        for student in students
    )
    return RenderedDocuments(
        template_pdf=render_pages((template_page,)),
        submissions_pdf=render_pages(student_pages),
    )
