from flask import Blueprint, session, redirect, url_for, flash, request, render_template, jsonify
from models import db, User, TWResponses, TWDocuments
from werkzeug.utils import secure_filename
import os
from datetime import datetime

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

    # Generate a unique filename: userID_initials_timestamp.jpg
    user_initial = user.name[0].upper()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{user.id}_{user_initial}_{timestamp}.jpg"
    filename = secure_filename(filename)

    # Save the file
    file_path = os.path.join(SIGNATURE_UPLOAD_FOLDER, filename)
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
    return jsonify({"message": "Form progress saved successfully!"}), 200


