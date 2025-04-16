from flask import Blueprint, session, redirect, url_for, flash, request, render_template, jsonify, send_file
from models import db, User, TWResponses, TWDocuments, RCLDocuments, RCLResponses, Request
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

    # Generate a unique filename: userID.jpg
    filename = f"{user.id}.jpg"
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

@form_bp.route("/changeMajor_form", methods=['GET', 'POST'])
def fill_changeMajor_form():
    return render_template("changeMajor_form.html")

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

        # Check if student_email exists in the User table
        user_exists = User.query.filter_by(email=response.email).first()

        if not user_exists:
            flash("Error: The email associated with this request does not exist in the system.", "danger")
            return redirect(url_for("form.fill_tw_form"))

        # Check if request already exists
        request_entry = Request.query.filter_by(student_email=response.email, request_type="TW").first()

        if not request_entry:
            # Create a new request if one doesn't exist
            new_request = Request(
                student_email=response.email,
                request_type="TW",
                semester=request.form.get("withdrawal_term"),
                year=request.form.get("year"),
                status="draft"
            )
            db.session.add(new_request)
            db.session.commit()
            response.request_id = new_request.id
        else:
            response.request_id = request_entry.id

        # Process file uploads
        files = request.files.getlist("supporting_documents")
        for file in files:
            if file and document_allowed_file(file.filename):
                filename = secure_filename(f"user_{user_id}_{file.filename}")
                file_path = os.path.join(DOCUMENTS_UPLOAD_FOLDER, filename)
                file.save(file_path)

                # Store each file in TWDocuments
                new_doc = TWDocuments(
                    response=response,
                    file_name=file.filename,
                    file_path=filename
                )
                db.session.add(new_doc)

        # Checkboxes - If key is missing, default to False
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

        response.department_id = "1"
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
    response.student_name = request.form.get("student_name") or response.student_name
    response.ps_id = request.form.get("student_id") or response.ps_id
    response.phone = request.form.get("phone") or response.phone
    response.email = request.form.get("email") or response.email
    response.program = request.form.get("program") or response.program
    response.academic_career = request.form.get("academic_career") or response.academic_career

    withdrawal_term = request.form.get("withdrawal_term") or response.withdrawal_term_fall or response.withdrawal_term_spring or response.withdrawal_term_summer
    response.withdrawal_term_fall = (withdrawal_term == "Fall") if withdrawal_term else response.withdrawal_term_fall
    response.withdrawal_term_spring = (withdrawal_term == "Spring") if withdrawal_term else response.withdrawal_term_spring
    response.withdrawal_term_summer = (withdrawal_term == "Summer") if withdrawal_term else response.withdrawal_term_summer

    year_str = request.form.get("year") or (str(response.withdrawal_year) if response.withdrawal_year else "")
    response.withdrawal_year = int(year_str) if year_str.isdigit() else response.withdrawal_year

    response.financial_aid_ack = ("financial_aid" in request.form) if "financial_aid" in request.form else response.financial_aid_ack
    response.international_students_ack = ("international_students" in request.form) if "international_students" in request.form else response.international_students_ack
    response.student_athlete_ack = ("student_athletes" in request.form) if "student_athletes" in request.form else response.student_athlete_ack
    response.veterans_ack = ("veterans" in request.form) if "veterans" in request.form else response.veterans_ack
    response.graduate_students_ack = ("graduate_students" in request.form) if "graduate_students" in request.form else response.graduate_students_ack
    response.doctoral_students_ack = ("doctoral_students" in request.form) if "doctoral_students" in request.form else response.doctoral_students_ack
    response.housing_ack = ("housing" in request.form) if "housing" in request.form else response.housing_ack
    response.dining_ack = ("dining" in request.form) if "dining" in request.form else response.dining_ack
    response.parking_ack = ("parking" in request.form) if "parking" in request.form else response.parking_ack
    response.last_updated = datetime.utcnow()
    
    response.department_id = "1"
    db.session.commit()

    #---------- This part down is for building the PDF ----------

    # Ensure the student_name is not None and has at least one name
    name_parts = (response.student_name or "").strip().split()

    # Assign default empty values if any name part is missing
    first = name_parts[0] if len(name_parts) > 0 else ""
    middle = name_parts[1] if len(name_parts) > 1 else ""
    last = name_parts[2] if len(name_parts) > 2 else ""



    try:
        doc = fitz.open("static/emptyforms/TW/TW.pdf")  # open pdf
        print("PDF successfully opened!")
    except Exception as e:
        print(f"Failed to open PDF: {e}")


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
        print("FIELD: ", field)
    # Prevent errors by ensuring initials exist before accessing
        initials = (first[0] if first else "") + (last[0] if last else "")
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

    if first or last:  # Only insert name if at least one part exists
        page.insert_text((120, 130), last, fontname=font, fontsize=size, color=color)
        page.insert_text((240, 130), first, fontname=font, fontsize=size, color=color)
        if middle:
            page.insert_text((360, 130), middle[0], fontname=font, fontsize=size, color=color)
    #"student_signature": (100, 738)
    current_date = datetime.utcnow().strftime("%m/%d/%Y")
    # Insert the formatted date into the PDF
    page.insert_text((295, 738), current_date, fontname=font, fontsize=size, color=color)

    filename = f"{user_id}.jpg"
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

    # Avoid accessing first[0] or last[0] if empty
    filename = f"{user_id}.pdf"
    filename = secure_filename(filename)

    # Define the path where the document should be saved
    save_path = os.path.join('static', 'documents', 'TW', filename)

    # Save the document (assuming 'doc' is a document object with a 'save' method)
    doc.save(save_path)


    return jsonify({"message": "Form progress saved successfully!"}), 200

@form_bp.route("/rcl_form", methods=['GET', 'POST'])
def fill_rcl_form():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    user_id = session["user"]["id"]
    # Try to load an existing draft
    existing_response = RCLResponses.query.filter_by(user_id=user_id, is_finalized=False).first()

    if request.method == 'POST':
        # If a draft exists, reuse it; otherwise create new
        response = existing_response if existing_response else RCLResponses(user_id=user_id)

        # 1) Handle multiple file uploads (if any)
        files = request.files.getlist("supporting_documents")
        for file in files:
            if file and document_allowed_file(file.filename):
                filename = secure_filename(f"user_{user_id}_{file.filename}")
                file_path = os.path.join(DOCUMENTS_UPLOAD_FOLDER, filename)
                file.save(file_path)

                # Link each file to the RCLResponses
                new_doc = RCLDocuments(
                    response=response,
                    file_name=file.filename,
                    file_path=filename
                )
                db.session.add(new_doc)

        # 2) Parse main_option (radio)
        main_option = request.form.get("main_option", "")
        # Convert radio choice into booleans on the RCLResponses model
        response.initial_adjustment_issues = (main_option == "IAI")
        response.improper_course_level_placement = (main_option == "ICLP")
        response.medical_reason = (main_option == "Medical Reason")
        response.final_semester = (main_option == "Final Semester")
        response.concurrent_enrollment = (main_option == "Concurrent Enrollment")

        # 3) Handle suboptions

        ## A) IAI suboptions
        if response.initial_adjustment_issues:
            suboptions = request.form.getlist("iai_suboption")  # e.g. ["English Language", "Reading Requirements"]
            # We can store them in initial_adjustment_explanation
            if suboptions:
                response.initial_adjustment_explanation = ", ".join(suboptions)
            else:
                response.initial_adjustment_explanation = None
        else:
            response.initial_adjustment_explanation = None

        ## B) Medical Reason suboption
        # If user selected "Medical Reason" and also checked "medical_confirmation"
        if response.medical_reason and "medical_confirmation" in request.form:
            response.medical_letter_attached = True
        else:
            response.medical_letter_attached = False

        ## C) Final Semester suboption
        if response.final_semester:
            # The user can enter the # of hours
            # Convert it safely to an integer
            final_hours_str = request.form.get("non_thesis_hours", "0")
            response.final_semester_hours_needed = int(final_hours_str) if final_hours_str.isdigit() else None
        else:
            response.final_semester_hours_needed = None

        ## D) Concurrent Enrollment suboption
        if response.concurrent_enrollment:
            uh_str = request.form.get("uh_hours", "0")
            other_str = request.form.get("other_school_hours", "0")
            response.concurrent_hours_uh = int(uh_str) if uh_str.isdigit() else None
            response.concurrent_hours_other = int(other_str) if other_str.isdigit() else None
            response.concurrent_university_name = request.form.get("other_school_name", "")
        else:
            response.concurrent_hours_uh = None
            response.concurrent_hours_other = None
            response.concurrent_university_name = None

        # 4) Additional fields: RCL semester & dropped courses
        # e.g. the user selects a semester: "fall" or "spring"
        sem = request.form.get("semester", "")
        response.semester_fall = (sem == "fall")
        response.semester_spring = (sem == "spring")

        # year
        year_str = request.form.get("year", "")
        # you might store it in e.g. response.year
        response.year_last_digit = None  # If you don't need this, remove it
        # Or store the entire year as integer
        if year_str.isdigit():
            # If the model has a year column
            # e.g. response.my_semester_year = int(year_str)
            pass

        # Dropped courses
        course1 = request.form.get("course1", "").strip()
        course2 = request.form.get("course2", "").strip()
        course3 = request.form.get("course3", "").strip()
        response.drop_courses = "; ".join([c for c in [course1, course2, course3] if c])

        # After drop: total_hours
        total_str = request.form.get("total_hours", "0")
        if total_str.isdigit():
            response.remaining_hours_uh = int(total_str)

        # 5) Basic fields (student info)
        response.student_name = request.form.get("student_name", "")
        response.ps_id = request.form.get("ps_id", "")
        response.email = request.form.get("email", "")
        response.student_signature = request.form.get("student_signature", "")
        # Possibly store the date if you have a column for it
        # e.g. response.submission_date = request.form.get("date", datetime.utcnow())

        user_email = session["user"]["email"]  # if you rely on the session email

        user_exists = User.query.filter_by(email=user_email).first()
        if not user_exists:
            flash("Error: The email associated with this request does not exist in the system.", "danger")
            return redirect(url_for("form.fill_rcl_form"))
        
        request_entry = Request.query.filter_by(
            student_email=user_email,
            request_type="RCL"
        ).first()

        if not request_entry:
            # If none, create a new Request
            new_request = Request(
                student_email=user_email,
                request_type="RCL",     # or "RCL_Grad" as needed
                semester=("fall" if response.semester_fall else "spring"),  # or None if you want
                year=year_str,          # or int(year_str) if you store it as int
                status="draft"          # default status
            )
            db.session.add(new_request)
            db.session.commit()
            response.request_id = new_request.id
        else:
            response.request_id = request_entry.id

        # 6) Check if form is finalized
        is_finalized = "confirm_acknowledgment" in request.form
        response.is_finalized = is_finalized
        response.last_updated = datetime.utcnow()

        response.department_id = "2"
        db.session.add(response)
        db.session.commit()

        # If user finalized the form, remove other drafts
        if is_finalized:
            RCLResponses.query.filter_by(user_id=user_id, is_finalized=False).delete()
            db.session.commit()
            flash("RCL Form submitted successfully!", "success")
            return redirect(url_for("dashboard"))

        flash("RCL Form saved successfully!", "success")
        return redirect(url_for("form.fill_rcl_form"))

    # If GET request, show the form with any existing data
    return render_template("rcl_form.html", response=existing_response)

@form_bp.route("/save_rcl_progress", methods=["POST"])
def save_rcl_progress():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]
    response = RCLResponses.query.filter_by(user_id=user_id, is_finalized=False).first()

    if not response:
        response = RCLResponses(user_id=user_id)
        db.session.add(response)

    # Parse main_option
    main_option = request.form.get("main_option", "")
    response.initial_adjustment_issues = (main_option == "IAI")
    response.improper_course_level_placement = (main_option == "ICLP")
    response.medical_reason = (main_option == "Medical Reason")
    response.final_semester = (main_option == "Final Semester")
    response.concurrent_enrollment = (main_option == "Concurrent Enrollment")

    # IAI suboptions
    if response.initial_adjustment_issues:
        suboptions = request.form.getlist("iai_suboption")  # e.g. ["English Language","Reading Requirements"]
        if suboptions:
            response.initial_adjustment_explanation = ", ".join(suboptions)
        else:
            response.initial_adjustment_explanation = None
    else:
        response.initial_adjustment_explanation = None

    # Medical Reason
    if response.medical_reason and "medical_confirmation" in request.form:
        response.medical_letter_attached = True
    else:
        response.medical_letter_attached = False

    # Final semester hours
    if response.final_semester:
        final_hours_str = request.form.get("non_thesis_hours", "0")
        response.final_semester_hours_needed = int(final_hours_str) if final_hours_str.isdigit() else None
    else:
        response.final_semester_hours_needed = None

    # Concurrent enrollment
    if response.concurrent_enrollment:
        uh_str = request.form.get("uh_hours", "0")
        other_str = request.form.get("other_school_hours", "0")
        response.concurrent_hours_uh = int(uh_str) if uh_str.isdigit() else None
        response.concurrent_hours_other = int(other_str) if other_str.isdigit() else None
        response.concurrent_university_name = request.form.get("other_school_name", "") or response.concurrent_university_name
    else:
        response.concurrent_hours_uh = None
        response.concurrent_hours_other = None
        response.concurrent_university_name = None

    # Additional fields
    response.student_name = request.form.get("student_name", "") or response.student_name
    response.ps_id = request.form.get("ps_id", "") or response.ps_id
    response.email = request.form.get("email", "") or response.email
    response.student_signature = request.form.get("student_signature", "") or response.student_signature

    # Semester info, etc.
    sem = request.form.get("semester", "")
    response.semester_fall = (sem == "fall")
    response.semester_spring = (sem == "spring")

    year_str = request.form.get("year", "0")
    # If you have 'year' or 'year_last_digit' in your DB:
    # response.my_semester_year = int(year_str) if year_str.isdigit() else None

    # Dropped courses
    course1 = request.form.get("course1", "").strip()
    course2 = request.form.get("course2", "").strip()
    course3 = request.form.get("course3", "").strip()
    response.drop_courses = "; ".join([c for c in [course1, course2, course3] if c])

    # total_hours => stored in remaining_hours_uh
    total_hrs = request.form.get("total_hours", "0")
    response.remaining_hours_uh = int(total_hrs) if total_hrs.isdigit() else None

    # year_hours
    year_hours_str = request.form.get("year_hours", "0")
    # e.g. response.year_hours = int(year_hours_str) if year_hours_str.isdigit() else None

    # last updated
    response.last_updated = datetime.utcnow()
    response.department_id = "2"
    db.session.commit()


    #---------- This part down is for building the PDF (Alex can you work on this) ----------

    student_map = {
        "initial_adjustment_explanation": (125.36, 251.52),
        "iclp_class1": (84.20, 354.36),
        "iclp_professor1": (227.12, 354.36),
        #"iclp_professor_signature1": (375.43, 354.36), TO BE ADDED
        "iclp_date1": (534.31, 354.36),
        "iclp_class2": (84.20, 370.44),
        "iclp_professor2": (227.12, 370.44),
        #"iclp_professor_signature2": (375.43, 370.44), TO BE ADDED
        "iclp_date2": (534.31, 370.44),
        "final_semester_hours_needed": (232.28, 507.72),
        "concurrent_hours_uh": (226.75, 572.77),
        "concurrent_hours_other": (318.21, 572.77),
        "concurrent_university_name": (375.44, 572.77),
        "fall_sem": (318.08, 604.68),
        "spring_sem": (453.68, 604.52),
        "dclass1": (198.08, 618.24), #seperated by semicolons in table
        "dclass2": (265.99, 618.24), #drop_courses = db.Column(db.String(255), nullable=True)
        "dclass3": (338.83, 618.24),
        "remaining_hours_uh": (79.16, 632.04),
        "fall_sem2": (271.65, 632.04),
        "spring_sem2": (406.40, 632.04),
        "student_name": (86.97, 688.70),
        "ps_id": (417.26, 688.70),
        #"AA1_name": (70.16, 725.16),
        #"AA1_sig": (286.27, 725.16), TO BE ADDED
        #"AA1_Date": (482.96, 725.16),
        #"AA2_name": (70.16, 760.80), 
        #"AA2_sig": (286.27, 760.80), TO BE ADDED
        #"AA2_date": (482.96, 760.80),

        "initial_adjustment_issues": (41.56, 240.32),
        "improper_course_level_placement": (41.56, 280.04),
        "medical_reason": (41.56, 402.44),
        #"medical_letter_attached": (54.76, 476.60), to be added
        "final_semester": (41.56, 508.16),
        "concurrent_enrollment": (41.56, 561.67),
        "semester_fall": (227.56, 605.11),
        "semester_spring": (351.64, 605.11),
        "semester_fall": (189.88, 632.48),
        "semester_spring": (302.68, 632.48)
    }


    #------ below os for oprinting pdf ----


        # Ensure the student_name is not None and has at least one name
    name_parts = (response.student_name or "").strip().split()

    # Assign default empty values if any name part is missing
    first = name_parts[0] if len(name_parts) > 0 else ""
    middle = name_parts[1] if len(name_parts) > 1 else ""
    last = name_parts[2] if len(name_parts) > 2 else ""

    doc = fitz.open("static/emptyforms/RCL/RCL.pdf") # open pdf

    # Choose the page to write on (0-indexed)
    page = doc.load_page(0)  # For the first page

    # Define text style (font, size, color, etc.)
    font = "helv"  # Use font name as string (e.g., 'helv' for Helvetica)
    size = 12  # Font size
    color = (0, 0, 0)  # Black color in RGB (0, 0, 0)

     # If the field exists (is not None), insert the value into the PDF
    # Iterate through the student_map
    # Iterate through the student_map
    for field, position in student_map.items():
        # Get the field value from the response object
        field_value = getattr(response, field, None)

    # Prevent errors by ensuring initials exist before accessing
        #print("FIELD: ", field, " FIELD_VALIE: ", field_value)
        if isinstance(field_value, bool):  # If the value is a boolean
            if field_value:  # If True,
                page.insert_text(position, "x", fontname=font, fontsize=size, color=color)
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

    #"student_signature": (100, 738)
    current_date = datetime.utcnow().strftime("%m/%d/%Y")
    # Insert the formatted date into the PDF
    page.insert_text((509.74, 688.70), current_date, fontname=font, fontsize=size, color=color)

    filename = f"{user_id}.jpg"
    filename = secure_filename(filename)

    # Save the file
    file_path = os.path.join("static/signatures", filename)

    # List all files in the SIGNATURE_UPLOAD_FOLDER
        # Position for student signature
    student_signature_position = (279.58, 640.70)  # The coordinates (x, y) where the signature will be inserted
    # Insert Student Signature (JPG image)
    try:
        img_rect = fitz.Rect(student_signature_position[0], student_signature_position[1], 
                            student_signature_position[0] + 100, student_signature_position[1] + 50)  # Adjust size if needed
        page.insert_image(img_rect, filename = file_path)
        #print("SUCCESS")
    except Exception as e:
        print(f"Error inserting student signature: {e}")

    user=session["user"]

    # Avoid accessing first[0] or last[0] if empty
    filename = f"{user_id}.pdf"
    filename = secure_filename(filename)

    # Define the path where the document should be saved
    save_path = os.path.join('static', 'documents', 'RCL', filename)

    # Save the document (assuming 'doc' is a document object with a 'save' method)
    doc.save(save_path)


    return jsonify({"message": "Form progress saved successfully!"}), 200

@form_bp.route("/preview_form", methods=["POST"])
def preview_form():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]
    form_type = request.form.get("form_type")  # Get the form type (TW or RCL)

    # Validate form type
    if form_type not in ["TW", "RCL"]:
        return jsonify({"error": "Invalid form type"}), 400

    # Call the appropriate save function
    if form_type == "TW":
        print("TEST1")
        save_tw_progress()
    elif form_type == "RCL":
        print("TEST1")
        save_rcl_progress()

    # Define the file name (Make sure your PDFs are saved in the right location)
    filename = f"{user_id}.pdf"
    filename = secure_filename(filename)

    # Construct the correct file path based on form type
    pdf_path = os.path.join('static', 'documents', form_type, filename)

    # Check if the file exists
    if not os.path.exists(pdf_path):
        return jsonify({"error": f"{form_type} PDF not found"}), 404

    # Return the existing PDF for display in the browser (opens in a new tab)
    return send_file(pdf_path, as_attachment=False, download_name=filename, mimetype="application/pdf")
    
@form_bp.route("/view_pdf/<int:request_id>")
def view_pdf(request_id):
    """Find and display the latest generated PDF for a request."""
    # Try to find an RCLResponses or TWResponses record
    request_entry = RCLResponses.query.get(request_id) or TWResponses.query.get(request_id)

    if not request_entry:
        flash("PDF not found!", "warning")
        return redirect(url_for("admin.admindashboard"))

    # Determine if it's RCL or TW
    if isinstance(request_entry, RCLResponses):
        form_type = "RCL"
    else:
        form_type = "TW"

    # Construct the PDF filename and path
    filename = f"{request_entry.user_id}.pdf"
    pdf_path = os.path.join("static", "documents", form_type, filename)
    print("TEST ", pdf_path)

    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype="application/pdf")

    flash("PDF not found!", "warning")
    return redirect(url_for("admin.admindashboard"))

@form_bp.route("/download_pdf/<int:request_id>")
def download_pdf(request_id):
    """Find and allow download of the generated PDF."""
    request_entry = RCLResponses.query.get(request_id) or TWResponses.query.get(request_id)

    if not request_entry:
        flash("PDF not found!", "warning")
        return redirect(url_for("admin.admindashboard"))

    # Distinguish RCL vs. TW
    if isinstance(request_entry, RCLResponses):
        form_type = "RCL"
    else:
        form_type = "TW"

    filename = f"{request_entry.user_id}.pdf"
    pdf_path = os.path.join("static", "documents", form_type, filename)

    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype="application/pdf", as_attachment=True)

    flash("PDF not found!", "warning")
    return redirect(url_for("admin.admindashboard"))