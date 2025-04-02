import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from io import BytesIO
import logging
import os
from datetime import datetime
import textwrap

# -------------------------------
# Helper functions
# -------------------------------
def load_codes(filename="codes.txt"):
    """Loads valid 4-digit codes from a text file."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return [int(line.strip()) for line in f if line.strip()]
    else:
        st.error(f"Codes file '{filename}' not found. Please create it in your project folder.")
        st.stop()

def update_codes(codes, filename="codes.txt"):
    """Rewrites the codes.txt file after removing used codes."""
    with open(filename, "w") as f:
        for code in codes:
            f.write(f"{code}\n")

def log_certificate_generation(code, name, roll_number, log_filename="certificate_log.txt"):
    """Logs certificate generation events (timestamp, code, name, roll number)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp},{code},{name},{roll_number}\n"
    with open(log_filename, "a") as log_file:
        log_file.write(log_line)

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Generate Certificate", "View Logs"])

if page == "Generate Certificate":
    st.title("Mentor Certificate Generator")
    st.write("Enter your details to generate your certificate.")

    # Load valid codes from file
    valid_codes = load_codes()

    # Input fields
    code_input = st.text_input("Enter your 4-digit code:", max_chars=4)
    name = st.text_input("Enter your full name:")
    roll_number = st.text_input("Enter your roll number:")

    if st.button("Generate Certificate"):
        if not code_input or not code_input.isdigit() or len(code_input) != 4:
            st.error("Please enter a valid 4-digit code.")
        else:
            code_val = int(code_input)
            if code_val not in valid_codes:
                st.error("Invalid or already used code. You are not eligible for a certificate.")
            elif not name or not roll_number:
                st.error("Please enter both your name and roll number.")
            else:
                # Remove used code and update file
                valid_codes.remove(code_val)
                update_codes(valid_codes)
                log_certificate_generation(code_val, name, roll_number)

                # Create the PDF in memory
                pdf_buffer = BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)
                page_width, page_height = letter  # 612 x 792 points

                # -----------------------------
                # 1) HEADER IMAGE
                # -----------------------------
                # Provide a valid path to your header image below:
                header_img_path = "header.png"  # e.g., "assets/header.png"
                # Adjust as needed:
                header_left = 0
                header_right = 0
                header_available_width = page_width - header_left - header_right
                header_height = 150  # Adjust to fit your image ratio

                if header_img_path:
                    # Draw the header image across the top
                    c.drawImage(
                        header_img_path,
                        header_left,
                        page_height - header_height - 20,
                        width=header_available_width,
                        height=header_height,
                        preserveAspectRatio=True
                    )
                    # Set the Y position below the header
                    current_y = page_height - header_height - 60
                else:
                    # If no header image is provided, use a placeholder text
                    c.setFont("Helvetica-Bold", 16)
                    c.drawCentredString(page_width / 2, page_height - 80, "Certificate of Acknowledgement")
                    current_y = page_height - 130


                def draw_inline_text(c, start_x, start_y, segments, max_x,
                                     line_height):
                    current_x = start_x
                    current_y = start_y
                    for text, font in segments:
                        c.setFont(font[0], font[1])
                        text_width = c.stringWidth(text, font[0], font[1])
                        # If this text would go beyond the right margin, wrap to the next line
                        if current_x + text_width > max_x:
                            current_y -= line_height
                            current_x = start_x
                        c.drawString(current_x, current_y, text)
                        current_x += text_width
                    return current_y


                # -----------------------------
                # Example layout settings
                # -----------------------------
                left_margin = 20
                right_margin = 20
                line_height = 18
                text_width = page_width - left_margin - right_margin
                max_x = left_margin + text_width

                # -----------------------------
                # Paragraph 1 (Part 1 & 2)
                # -----------------------------
                # We use a text object for these first two parts (regular text and bold name).
                para1_part1 = "This is to acknowledge that "

                text_obj = c.beginText()
                text_obj.setLeading(line_height)
                text_obj.setTextOrigin(left_margin, current_y)
                text_obj.setFont("Helvetica", 12)

                # Part 1: normal text
                for line in textwrap.wrap(para1_part1, width=100):
                    text_obj.textLine(line)

                # Part 2: bold name & roll number
                text_obj.setFont("Helvetica-Bold", 12)
                bold_name_line = f"{name} ({roll_number})"
                for line in textwrap.wrap(bold_name_line, width=100):
                    text_obj.textLine(line)

                # Flush these lines to the canvas
                c.drawText(text_obj)

                # Update current_y to the end of what we just drew
                current_y = text_obj.getY()
                # Move down one extra line to create space
                # current_y -= line_height

                # -----------------------------
                # Paragraph 1 (Part 3) with inline bold words
                # -----------------------------
                # We'll build segments for:
                # "served as a " (normal),
                # "Mentor" (bold),
                # " in the " (normal),
                # "MentorLink Programme" (bold), etc.
                segments = [
                    ("served as a ", ("Helvetica", 12)),
                    ("Mentor", ("Helvetica-Bold", 12)),
                    (" in the ", ("Helvetica", 12)),
                    ("MentorLink Programme", ("Helvetica-Bold", 12)),
                    (" conducted by ", ("Helvetica", 12)),
                    ("STEP DTU", ("Helvetica-Bold", 12)),
                    (" during the academic year ", ("Helvetica", 12)),
                    ("2024-2025", ("Helvetica-Bold", 12)),
                    (".", ("Helvetica", 12))
                ]

                # Draw them on one or more lines as needed
                current_y = draw_inline_text(c, left_margin, current_y,
                                             segments, max_x, line_height)
                # Move down a blank line after finishing Part 3
                current_y -= line_height

                # -----------------------------
                # Paragraph 2 & 3
                # -----------------------------
                # We switch back to a text object approach for normal paragraphs
                text_obj = c.beginText()
                text_obj.setLeading(line_height)
                text_obj.setTextOrigin(left_margin, current_y)
                text_obj.setFont("Helvetica", 12)

                para2 = (
                    "Their consistent efforts, guidance, and valuable contributions "
                    "towards supporting and mentoring juniors are truly appreciated."
                )
                for line in textwrap.wrap(para2, width=100):
                    text_obj.textLine(line)
                text_obj.textLine("")  # blank line after paragraph 2

                para3 = (
                    "Their role has been instrumental in fostering a culture of growth, "
                    "empathy, and peer learning at DTU."
                )
                for line in textwrap.wrap(para3, width=100):
                    text_obj.textLine(line)
                text_obj.textLine("")  # blank line after paragraph 3

                # Draw paragraphs 2 & 3
                c.drawText(text_obj)
                current_y = text_obj.getY()

                # "Issued by" block
                text_obj.setFont("Helvetica-Bold", 12)
                text_obj.textLine("Issued by:")
                text_obj.textLine("STEP DTU Society")
                text_obj.setFont("Helvetica", 12)
                text_obj.textLine("Delhi Technological University")

                c.drawText(text_obj)

                # -----------------------------
                # 3) FOOTER SIGNATURES (Optional)
                # -----------------------------
                # If you have signatures, place them near the bottom:
                footer_y = 110
                margin = 50
                available_width = page_width - 2 * margin
                first_x = margin + available_width / 6
                second_x = margin + available_width / 2
                third_x = margin + 5 * available_width / 6

                signature_width = 100
                signature_height = 60

                # Provide valid paths to your signature images if you have them:
                signature1_path = "divyansh_sign.jpg"  # e.g., "assets/signature1.png"
                signature2_path = "chaitanya_sign.png"  # e.g., "assets/signature2.png"
                signature3_path = "Sushant_Sign.png"  # e.g., "assets/signature3.png"

                if signature1_path:
                    c.drawImage(
                        signature1_path,
                        first_x - signature_width / 2,
                        footer_y,
                        width=signature_width,
                        height=signature_height,
                        preserveAspectRatio=True
                    )
                if signature2_path:
                    c.drawImage(
                        signature2_path,
                        second_x - signature_width / 2,
                        footer_y,
                        width=signature_width,
                        height=signature_height,
                        preserveAspectRatio=True
                    )
                if signature3_path:
                    c.drawImage(
                        signature3_path,
                        third_x - signature_width / 2,
                        footer_y,
                        width=signature_width,
                        height=signature_height,
                        preserveAspectRatio=True
                    )

                # Names & Designations below signatures
                names_y = footer_y - 15
                designations_y = footer_y - 30
                c.setFont("Helvetica-Bold", 10)
                c.drawCentredString(first_x, names_y, "Divyansh Khandelwal")
                c.drawCentredString(second_x, names_y, "Chaitanya Anand")
                c.drawCentredString(third_x, names_y, "Sushant Nagi")

                c.setFont("Helvetica", 10)
                c.drawCentredString(first_x, designations_y, "(President)")
                c.drawCentredString(second_x, designations_y, "(Vice President)")
                c.drawCentredString(third_x, designations_y, "(Project Head)")

                # Finish up
                c.showPage()
                c.save()
                pdf_buffer.seek(0)

                st.download_button(
                    label="Download your certificate",
                    data=pdf_buffer,
                    file_name="certificate.pdf",
                    mime="application/pdf"
                )
                st.success("Your certificate has been generated!")

elif page == "View Logs":
    st.title("Certificate Generation Logs")
    st.write("Below are the logs of certificate generations (Name, Roll Number, Code, Timestamp):")
    log_filename = "certificate_log.txt"
    if os.path.exists(log_filename):
        with open(log_filename, "r") as log_file:
            log_lines = log_file.readlines()
        if log_lines:
            log_data = []
            for line in log_lines:
                # Format: timestamp,code,name,roll_number
                parts = line.strip().split(",")
                if len(parts) == 4:
                    log_data.append({
                        "Timestamp": parts[0],
                        "Code": parts[1],
                        "Name": parts[2],
                        "Roll Number": parts[3]
                    })
            st.table(log_data)
        else:
            st.write("No logs available yet.")
    else:
        st.write("No log file found.")
