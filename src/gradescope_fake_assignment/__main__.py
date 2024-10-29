import argparse
import pandas as pd
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from pikepdf import Pdf, Page

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate Gradescope PDF submissions.")
    parser.add_argument("assignment_name", type=str, help="Name of the assignment.")
    parser.add_argument("csv_path", type=str, help="Path to the CSV file with student roster.")
    parser.add_argument("--format", type=str, choices=["standard", "custom"], default="standard",
                        help="Specify the format of the roster CSV.")
    parser.add_argument("--output_dir", type=str, default=".", help="Directory to save output PDFs.")
    return parser.parse_args()

def load_roster(csv_path, format):
    if format == "standard":
        roster = pd.read_csv(csv_path, usecols=["Name"])
    elif format == "custom":
        roster = pd.read_csv(csv_path, usecols=["Full Name"])
        roster.columns = ["Name"]  # Standardize column names for consistency
    else:
        raise ValueError("Unsupported format.")
    return roster["Name"].tolist()

def create_template_pdf(assignment_name, output_path):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    c.drawString(100, 700, f"Assignment: {assignment_name}")
    c.drawString(100, 650, "Student: ___________________________")  # Placeholder for OCR
    c.showPage()
    c.save()

def create_student_pdf(assignment_name, student_name, output_path):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    c.drawString(100, 700, f"Assignment: {assignment_name}")
    c.drawString(100, 650, f"Student: {student_name}")
    c.showPage()
    c.save()

def combine_pdfs(template_path, student_names, assignment_name, output_path):
    # Initialize the combined PDF
    combined_pdf = Pdf.new()

    # Add template as the first page
    with Pdf.open(template_path) as template_pdf:
        combined_pdf.pages.append(template_pdf.pages[0])

    # Add each student's submission as a new page
    for student_name in student_names:
        student_pdf_path = f"{output_path}/{student_name}_submission.pdf"
        create_student_pdf(assignment_name, student_name, student_pdf_path)

        with Pdf.open(student_pdf_path) as student_pdf:
            combined_pdf.pages.append(student_pdf.pages[0])

    # Save the combined submissions PDF
    combined_pdf.save(f"{output_path}/submissions.pdf")

def main():
    args = parse_arguments()

    # Step 1: Load the student roster
    student_names = load_roster(args.csv_path, args.format)

    # Step 2: Create a template PDF for Gradescope
    template_pdf_path = f"{args.output_dir}/template.pdf"
    create_template_pdf(args.assignment_name, template_pdf_path)

    # Step 3: Generate combined student submissions PDF
    combined_pdf_path = f"{args.output_dir}/submissions.pdf"
    combine_pdfs(template_pdf_path, student_names, args.assignment_name, args.output_dir)

    print(f"Template PDF created at: {template_pdf_path}")
    print(f"Submissions PDF created at: {combined_pdf_path}")

if __name__ == "__main__":
    main()
