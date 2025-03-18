from flask import Blueprint, session, redirect, url_for, flash, request, render_template, jsonify
from models import db, User, TWResponses, TWDocuments
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import fitz

form_bp = Blueprint("form", __name__)

# Allowed extensions
SIGNATURE_ALLOWED_EXTENSIONS = {"jpg", "jpeg"}
SIGNATURE_UPLOAD_FOLDER = "static/signatures"
DOCUMENTS_ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
DOCUMENTS_UPLOAD_FOLDER = "static/documents"

# Ensure upload folder exists
if not os.path.exists(SIGNATURE_UPLOAD_FOLDER):
    os.makedirs(SIGNATURE_UPLOAD_FOLDER)

# Ensure upload folder exists
if not os.path.exists(DOCUMENTS_UPLOAD_FOLDER):
    os.makedirs(DOCUMENTS_UPLOAD_FOLDER)

def signature_allowed_file(filename):
    """ Check if the file has a valid extension """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in SIGNATURE_ALLOWED_EXTENSIONS

def document_allowed_file(filename):
    """ Check if the file has a valid extension """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in DOCUMENTS_ALLOWED_EXTENSIONS


# Upload signature page
@form_bp.route("/upload_signature_page")
def upload_signature_page():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))
    
    return render_template("upload_signature.html")

@form_bp.route("/upload_signature", methods=["POST"])
def upload_signature():
    if "user" not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for("home"))

    if "signature" not in request.files or request.files["signature"].filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("upload_signature_page"))

    file = request.files["signature"]

    if not signature_allowed_file(file.filename):
        flash("Invalid file type! Only JPG and JPEG are allowed.", "danger")
        return redirect(url_for("upload_signature_page"))

    # Retrieve user from session
    user = User.query.filter_by(email=session["user"]["email"]).first()
    if not user:
        flash("User not found!", "danger")
        return redirect(url_for("home"))

    # Generate a unique filename: userID_initials.jpg
    user_initial = user.name[0].upper()
    filename = f"{user.id}_{user_initial}.jpg"
    filename = secure_filename(filename)


    # Save the file
    file_path = os.path.join("static/signatures", filename)
    file.save(file_path)

    # Update user's signature path in the database
    user.signature_path = f"signatures/{filename}"
    user.updated_at = datetime.utcnow()
    db.session.commit()

    # Update session data
    session["user"]["signature_path"] = user.signature_path
    session.modified = True

    flash("Signature uploaded successfully!", "success")
    return redirect(url_for("dashboard"))

@form_bp.route("/tw_form", methods=['GET', 'POST'])
def fill_tw_form():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    user_id = session["user"]["id"]
    existing_response = TWResponses.query.filter_by(user_id=user_id, is_finalized=False).first()

    if request.method == 'POST':
        response = existing_response if existing_response else TWResponses(user_id=user_id)

        # Ensure is not None, default to empty string
        response.student_name = request.form.get("student_name", "").strip() or ""
        response.email = request.form.get("email", "").strip() or ""
        response.ps_id = request.form.get("student_id", "").strip() or ""
        response.phone = request.form.get("phone", "").strip() or ""
        response.program = request.form.get("program", "").strip() or ""
        response.academic_career = request.form.get("academic_career", "").strip() or ""

        files = request.files.getlist("supporting_documents")  # Because 'multiple' is used
        for file in files:
            if file and document_allowed_file(file.filename):
                filename = secure_filename(f"user_{user_id}_{file.filename}")
                file_path = os.path.join(DOCUMENTS_UPLOAD_FOLDER, filename)
                file.save(file_path)

                # Store each file in TWDocuments
                new_doc = TWDocuments(
                    response=response,
                    file_name=file.filename,
                    file_path=filename  # store relative path or full path
                )
                db.session.add(new_doc)

        # Text Inputs
        response.student_name = request.form.get("student_name")
        response.ps_id = request.form.get("student_id")
        response.phone = request.form.get("phone")
        response.email = request.form.get("email")
        response.program = request.form.get("program")
        response.academic_career = request.form.get("academic_career")

        # Fix Checkboxes - If key is missing, default to False
        response.financial_aid_ack = "financial_aid" in request.form
        response.international_students_ack = "international_students" in request.form
        response.student_athlete_ack = "student_athletes" in request.form
        response.veterans_ack = "veterans" in request.form
        response.graduate_students_ack = "graduate_students" in request.form
        response.doctoral_students_ack = "doctoral_students" in request.form
        response.housing_ack = "housing" in request.form
        response.dining_ack = "dining" in request.form
        response.parking_ack = "parking" in request.form

        # Fix Dropdown
        withdrawal_term = request.form.get("withdrawal_term")
        response.withdrawal_term_fall = withdrawal_term == "Fall"
        response.withdrawal_term_spring = withdrawal_term == "Spring"
        response.withdrawal_term_summer = withdrawal_term == "Summer"
        response.withdrawal_year = request.form.get("year")

        # Track last update
        response.last_updated = datetime.utcnow()

        # Check if form is finalized
        is_finalized = "confirm_acknowledgment" in request.form
        response.is_finalized = is_finalized

        db.session.add(response)
        db.session.commit()

        # If finalized, remove any unfinished drafts
        if is_finalized:
            TWResponses.query.filter_by(user_id=user_id, is_finalized=False).delete()
            db.session.commit()
            flash("Form submitted successfully!", "success")
            return redirect(url_for("dashboard"))

        flash("Form saved successfully!", "success")
        return redirect(url_for("form.fill_tw_form"))

    return render_template("tw_form.html", response=existing_response)


@form_bp.route("/save_tw_progress", methods=["POST"])
def save_tw_progress():
    """Saves the current form progress asynchronously."""
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]

    # Check for existing draft
    response = TWResponses.query.filter_by(user_id=user_id, is_finalized=False).first()
    
    if not response:
        response = TWResponses(user_id=user_id)
        db.session.add(response)

    # Update with form data

    # Correctly get the text value from the form:
    response.student_name = request.form.get("student_name", "")
    response.ps_id = request.form.get("student_id", "")
    response.phone = request.form.get("phone", "")
    response.email = request.form.get("email", "")
    response.program = request.form.get("program", "")
    response.academic_career = request.form.get("academic_career", "")

    withdrawal_term = request.form.get("withdrawal_term", "")
    response.withdrawal_term_fall = (withdrawal_term == "Fall")
    response.withdrawal_term_spring = (withdrawal_term == "Spring")
    response.withdrawal_term_summer = (withdrawal_term == "Summer")

    year_str = request.form.get("year", "")
    response.withdrawal_year = int(year_str) if year_str.isdigit() else None

    response.financial_aid_ack = "financial_aid" in request.form
    response.international_students_ack = "international_students" in request.form
    response.student_athlete_ack = "student_athletes" in request.form
    response.veterans_ack = "veterans" in request.form
    response.graduate_students_ack = "graduate_students" in request.form
    response.doctoral_students_ack = "doctoral_students" in request.form
    response.housing_ack = "housing" in request.form
    response.dining_ack = "dining" in request.form
    response.parking_ack = "parking" in request.form

    response.last_updated = datetime.utcnow()

    db.session.commit()




    #---------- This part down is for building the PDF ----------





    first, middle, last = response.student_name.split()

   #print("TEST: ", first, middle, last)

    doc = fitz.open("static/emptyforms/TW/TW.pdf") # open pdf

    # Choose the page to write on (0-indexed)
    page = doc.load_page(0)  # For the first page

    # Define text style (font, size, color, etc.)
    font = "helv"  # Use font name as string (e.g., 'helv' for Helvetica)
    size = 12  # Font size
    color = (0, 0, 0)  # Black color in RGB (0, 0, 0)

    # Define the student map with coordinates
    student_map = {
        "ps_id": (480, 130),
        "phone": (100, 150),
        "email": (300, 150),
        "program": (120, 167),
        "academic_career": (460, 167),

        # Withdrawal Term
        "withdrawal_term_fall": (203, 187), #Fall
        "withdrawal_term_spring": (253, 187), #spring
        "withdrawal_term_summer": (308, 187), #summer
        "withdrawal_year": (115, 187),

        # Initial Acknowledgments
        "financial_aid_ack": (50, 265), #fin aid
        "international_students_ack": (50, 300), #internationl stu
        "student_athlete_ack": (50, 350), #student_athlete_ack
        "veterans_ack": (50, 405), #veterans_ack
        "graduate_students_ack": (50, 440), #graduate_students_ack
        "doctoral_students_ack": (50, 465), #doctoral_students_ack
        "housing_ack": (50, 500), #housing_ack
        "dining_ack": (50, 545), #dining_ack
        "parking_ack": (50, 590), #parking_ack
    }
  
    # If the field exists (is not None), insert the value into the PDF
    # Iterate through the student_map
# Iterate through the student_map
    for field, position in student_map.items():
        # Get the field value from the response object
        field_value = getattr(response, field, None)
        initials = first[0] + last[0]
        #print("FIELD: ", field, " FIELD_VALIE: ", field_value)
        if isinstance(field_value, bool):  # If the value is a boolean
            if field_value:  # If True,
                    if field == "withdrawal_term_fall" or field == "withdrawal_term_spring" or field == "withdrawal_term_summer":  # For Fall term, output "X" if True, initials if False
                        page.insert_text(position, "x", fontname=font, fontsize=size, color=color)
                    else:
                        page.insert_text(position, initials, fontname=font, fontsize=size, color=color)
            else:  # If False, output nothing
                page.insert_text(position, " ", fontname=font, fontsize=size, color=color)
        elif isinstance(field_value, (str, int)):  # If the value is a string or integer
            if field_value:  # If the string or integer is not empty
                #print("FIELD: ", field, " FIELD_VALUE: ", field_value)
                page.insert_text(position, str(field_value), fontname=font, fontsize=size, color=color)
            else:  # If the string is empty, output nothing
                page.insert_text(position, " ", fontname=font, fontsize=size, color=color)

    # Handle other cases if needed
    else:
        page.insert_text(position, " ", fontname=font, fontsize=size, color=color)


    #"last_name" : (120, 130)
    page.insert_text((120, 130), last, fontname=font, fontsize=size, color=color)
    #"first_name": (240, 130)
    page.insert_text((240, 130), first, fontname=font, fontsize=size, color=color)
    #"middle_init": (360, 130)
    page.insert_text((360, 130), middle[0], fontname=font, fontsize=size, color=color)
    #"student_signature": (100, 738)
    current_date = datetime.utcnow().strftime("%m/%d/%Y")
    # Insert the formatted date into the PDF
    page.insert_text((295, 738), current_date, fontname=font, fontsize=size, color=color)

    filename = f"{user_id}_{last[0]}.jpg"
    filename = secure_filename(filename)

    # Save the file
    file_path = os.path.join("static/signatures", filename)

    # List all files in the SIGNATURE_UPLOAD_FOLDER
        # Position for student signature
    student_signature_position = (100, 720)  # The coordinates (x, y) where the signature will be inserted
    # Insert Student Signature (JPG image)
    try:
        img_rect = fitz.Rect(student_signature_position[0], student_signature_position[1], 
                            student_signature_position[0] + 100, student_signature_position[1] + 50)  # Adjust size if needed
        page.insert_image(img_rect, filename = file_path)
        print("SUCCESS")
    except Exception as e:
        print(f"Error inserting student signature: {e}")




    user=session["user"]

    user_initial = first[0].upper()
    filename = f"{user_id}_{user_initial}.pdf"
    filename = secure_filename(filename)

    # Define the path where the document should be saved
    save_path = os.path.join('static', 'documents', filename)

    # Save the document (assuming 'doc' is a document object with a 'save' method)
    doc.save(save_path)



    return jsonify({"message": "Form progress saved successfully!"}), 200

@form_bp.route("/preview_TW", methods = ["POST"])
def preview_TW():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]

    # Check for existing draft
    response = TWResponses.query.filter_by(user_id=user_id, is_finalized=False).first()
    
    if not response:
        response = TWResponses(user_id=user_id)
        db.session.add(response)

    # Update with form data

    # Correctly get the text value from the form:
    response.student_name = request.form.get("student_name", "")
    response.ps_id = request.form.get("student_id", "")
    response.phone = request.form.get("phone", "")
    response.email = request.form.get("email", "")
    response.program = request.form.get("program", "")
    response.academic_career = request.form.get("academic_career", "")

    withdrawal_term = request.form.get("withdrawal_term", "")
    response.withdrawal_term_fall = (withdrawal_term == "Fall")
    response.withdrawal_term_spring = (withdrawal_term == "Spring")
    response.withdrawal_term_summer = (withdrawal_term == "Summer")

    year_str = request.form.get("year", "")
    response.withdrawal_year = int(year_str) if year_str.isdigit() else None

    response.financial_aid_ack = "financial_aid" in request.form
    response.international_students_ack = "international_students" in request.form
    response.student_athlete_ack = "student_athletes" in request.form
    response.veterans_ack = "veterans" in request.form
    response.graduate_students_ack = "graduate_students" in request.form
    response.doctoral_students_ack = "doctoral_students" in request.form
    response.housing_ack = "housing" in request.form
    response.dining_ack = "dining" in request.form
    response.parking_ack = "parking" in request.form

    response.last_updated = datetime.utcnow()

    #thsi block splits the full given name into individual

    



    return 0
