import argparse
import os
import pandas as pd
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from pikepdf import Pdf

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate Gradescope PDF submissions.")
    parser.add_argument("assignment_name", type=str, help="Name of the assignment.")
    parser.add_argument("csv_path", type=str, help="Path to the CSV file with student roster.")
    parser.add_argument("--format", type=str, choices=["standard", "custom"], default="standard",
                        help="Specify the format of the roster CSV.")
    parser.add_argument("--output_dir", type=str, default=".", help="Directory to save output PDFs.")
    return parser.parse_args()

def load_roster(csv_path, format):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file '{csv_path}' does not exist.")

    # Define required columns for each format
    required_columns = ["First Name", "Last Name"] if format == "standard" else ["Name"]

    # Read the CSV and validate headers without reloading
    roster = pd.read_csv(csv_path)
    missing_columns = [col for col in required_columns if col not in roster.columns]
    if missing_columns:
        raise ValueError(f"CSV file is missing the required column(s): {', '.join(missing_columns)}")

    # Extract names based on format
    if format == "standard":
        roster["Name"] = roster["First Name"] + " " + roster["Last Name"]
    else:
        roster.rename(columns={"Full Name": "Name"}, inplace=True)

    return roster["Name"].tolist()

def create_template_pdf(assignment_name, output_path):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    c.drawString(100, 700, f"Assignment: {assignment_name}")
    c.drawString(100, 650, "Student:")
    c.line(150, 645, 400, 645)  # Draws a long underline for the template
    c.showPage()
    c.save()

def create_student_pdf(assignment_name, student_name, output_path):
    c = canvas.Canvas(output_path, pagesize=LETTER)
    c.drawString(100, 700, f"Assignment: {assignment_name}")
    c.drawString(100, 650, "Student:")

    text_width = c.stringWidth(student_name, "Helvetica", 12)
    c.drawString(150, 650, student_name)  # Place student name at starting position
    c.line(150, 645, 150 + text_width, 645)  # Underline of exact width below name
    c.showPage()
    c.save()

def combine_pdfs(student_names, assignment_name, output_dir):
    # Ensure submissions.pdf is safely overwritten at the end of processing
    combined_pdf_path = f"{output_dir}/submissions.pdf"
    temp_student_pdfs = []

    combined_pdf = Pdf.new()
    for idx, student_name in enumerate(student_names):
        safe_student_name = student_name.replace(" ", "_").replace("/", "_")
        student_pdf_path = f"{output_dir}/{safe_student_name}_{idx}_submission.pdf"
        temp_student_pdfs.append(student_pdf_path)  # Track for cleanup

        # Create individual student PDF and add it to combined PDF
        create_student_pdf(assignment_name, student_name, student_pdf_path)
        with Pdf.open(student_pdf_path) as student_pdf:
            combined_pdf.pages.append(student_pdf.pages[0])

    # Save combined PDF after successfully adding all pages
    combined_pdf.save(combined_pdf_path)

    # Delete temporary student PDFs
    for pdf in temp_student_pdfs:
        os.remove(pdf)

    print(f"Submissions PDF created at: {combined_pdf_path}")

def main():
    print("Generating Gradescope PDFs...")
    args = parse_arguments()

    # Ensure output directory exists
    if not os.path.exists(args.output_dir):
        print(f"Output directory '{args.output_dir}' does not exist. Creating it...")
        os.makedirs(args.output_dir)

    # Load student names from CSV roster
    try:
        student_names = load_roster(args.csv_path, args.format)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return

    # Create the Gradescope template PDF
    template_pdf_path = f"{args.output_dir}/template.pdf"
    create_template_pdf(args.assignment_name, template_pdf_path)
    print(f"Template PDF created at: {template_pdf_path}")

    # Generate combined student submissions PDF
    combine_pdfs(student_names, args.assignment_name, args.output_dir)

if __name__ == "__main__":
    main()
