from flask import Blueprint, session, redirect, url_for, flash, request, render_template, jsonify, send_file
from models import db, User, TWResponses, TWDocuments, RCLDocuments, RCLResponses, GeneralPetition, GeneralPetitionDocuments, ApprovalProcess, CAResponses
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

@form_bp.route("/cm_form", methods=['GET', 'POST'])
def fill_cm_form():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    user_id = session["user"]["id"]
    existing_response = GeneralPetition.query.filter_by(user_id=user_id, is_finalized=False).first()

    if request.method == 'POST':
        response = existing_response if existing_response else GeneralPetition(user_id=user_id)

        response.student_last_name   = request.form.get("last_name",   "").strip()
        response.student_first_name  = request.form.get("first_name",  "").strip()
        response.student_middle_name = request.form.get("middle_name", "").strip()
        response.student_uh_id       = request.form.get("uh_id",       "").strip()
        response.student_phone_number= request.form.get("phone",       "").strip()
        response.student_mailing_address = request.form.get("mailing_address","").strip()
        response.student_city        = request.form.get("city",        "").strip()
        response.student_state       = request.form.get("state",       "").strip()
        response.student_zip_code    = request.form.get("zip",         "").strip()
        response.student_email       = request.form.get("email",       "").strip()

        response.Q1 = "Q1" in request.form
        response.program_status_action = request.form.get("update_status_action","").strip()

        response.Q2 = "Q2" in request.form
        response.admission_status_from = request.form.get("admission_status_from","").strip()
        response.admission_status_to   = request.form.get("admission_status_to","").strip()

        response.Q3 = "Q3" in request.form
        response.new_career            = request.form.get("new_career","").strip()
        # post‑bac study‑objective radio buttons
        response.second_bachelor_plan        = request.form.get("study_objective") == "second_degree"
        response.graduate_study_objective    = request.form.get("study_objective") == "grad_study"
        response.teacher_certification       = request.form.get("study_objective") == "teacher_cert"
        response.personal_enrichment_objective= request.form.get("study_objective") == "enrichment"

        response.Q4 = "Q4" in request.form
        response.program_change_from = request.form.get("program_change_from","").strip()
        response.program_change_to   = request.form.get("program_change_to","").strip()

        response.Q5 = "Q5" in request.form
        response.plan_change_from = request.form.get("plan_change_from","").strip()
        response.plan_change_to   = request.form.get("plan_change_to","").strip()

        response.Q6 = "Q6" in request.form
        response.degree_objective_change_from = request.form.get("degree_objective_change_from","").strip()
        response.degree_objective_change_to   = request.form.get("degree_objective_change_to","").strip()

        response.Q7 = "Q7" in request.form
        response.requirement_term_catalog      = request.form.get("requirement_term_catalog","").strip()
        response.requirement_term_program_plan = request.form.get("requirement_term_program_plan","").strip()

        response.Q8 = "Q8" in request.form
        response.additional_plan_degree_type        = request.form.get("additional_plan_degree_type","").strip()
        response.additional_plan_degree_type_other  = request.form.get("additional_plan_degree_type_other","").strip()
        response.primary_plan   = request.form.get("primary_plan")   == "primary_plan"
        response.secondary_plan = request.form.get("secondary_plan") == "secondary_plan"

        response.Q9  = "Q9" in request.form
        response.second_degree_type = request.form.get("second_degree_type","").strip()

        response.Q10 = "Q10" in request.form
        response.minor_change_from = request.form.get("minor_change_from","").strip()
        response.minor_change_to   = request.form.get("minor_change_to","").strip()

        response.Q11 = "Q11" in request.form
        response.additional_minor = request.form.get("additional_minor","").strip()

        # Q12 – Q17 are just flags; any details could go in explanation
        for i in range(12, 18):
            setattr(response, f"Q{i}", f"Q{i}" in request.form)

        response.explanation = request.form.get("explanation","").strip()
        response.student_signature = request.form.get("student_signature","").strip()
        response.signature_date    = request.form.get("date") or None

        files = request.files.getlist("supporting_documents")
        for f in files:
            if f and document_allowed_file(f.filename):
                safe = secure_filename(f"user_{user_id}_{f.filename}")
                path = os.path.join(DOCUMENTS_UPLOAD_FOLDER, safe)
                f.save(path)

                response.documents.append(
                    GeneralPetitionDocuments(
                        file_name = f.filename,
                        file_path = safe
                    )
                )

        # -------------------- 6️⃣  MISC / BOOK‑KEEPING ---------------
        response.last_updated  = datetime.utcnow()
        response.department_id =  3         # or whichever dept. you need
        response.approval_status = 1                  # 1 = draft / waiting
                                                   
        # 4️⃣ Is the form finalized?
        is_finalized = "confirm_acknowledgment" in request.form
        response.is_finalized = is_finalized 

        db.session.add(response)
        db.session.commit()

        # 5️⃣ If finalized, clean up drafts and start the approval flow ⬅️
        if is_finalized:
            # 1️⃣  Delete every other GeneralPetition from *this* user
            (db.session.query(GeneralPetition)
                .filter(
                    GeneralPetition.user_id == user_id,
                    GeneralPetition.id != response.id        # keep the one we just saved
                )
                .delete(synchronize_session="fetch")         # or "False" for speed
            )

            # Mark this response as “submitted / pending approval”
            response.approval_status = 2   # 2 = submitted, waiting for approver
            db.session.add(response) 
            db.session.commit()

            # Create an ApprovalProcess record
            approval = ApprovalProcess(
                user_id   = response.user_id,    # student
                approver_id = session["user"]["id"],   # whoever is submitting
                form_type = 3,                    # 3 = CM petition
                status    = "pending",
                decision_date = datetime.utcnow(),
                comments  = None,
            )
            db.session.add(approval)
            db.session.commit()

            flash("Petition submitted successfully!", "success")
            return redirect(url_for("dashboard")) 

        flash("Petition saved successfully!", "success")
        return redirect(url_for("form.fill_cm_form"))

    # GET – render template with any draft pre‑filled
    return render_template("cm_form.html", response=existing_response)

@form_bp.route("/save_cm_progress", methods=["POST"])
def save_cm_progress():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]

    response = GeneralPetition.query.filter_by(user_id=user_id, is_finalized=False).first()
    if not response:
        response = GeneralPetition(user_id=user_id)
        db.session.add(response)

    # === Student Info ===
    response.student_last_name = request.form.get("last_name", response.student_last_name)
    response.student_first_name = request.form.get("first_name", response.student_first_name)
    response.student_middle_name = request.form.get("middle_name", response.student_middle_name)
    response.student_uh_id = request.form.get("uh_id", response.student_uh_id)
    response.student_phone_number = request.form.get("phone", response.student_phone_number)
    response.student_mailing_address = request.form.get("mailing_address", response.student_mailing_address)
    response.student_city = request.form.get("city", response.student_city)
    response.student_state = request.form.get("state", response.student_state)
    response.student_zip_code = request.form.get("zip", response.student_zip_code)
    response.student_email = request.form.get("email", response.student_email)

    # === Petition Purpose Flags ===
    #testing
    for i in range(1, 18):
        print(f"TESTING Q{i}: {request.form.get(f'Q{i}', 'Not in form')} , response: {getattr(response, f'Q{i}', 'No attr')}")
        setattr(response, f"Q{i}", f"Q{i}" in request.form)

    # === Petition Purpose Details ===
    response.program_status_action = request.form.get("update_status_action", response.program_status_action)
    response.admission_status_from = request.form.get("admission_status_from", response.admission_status_from)
    response.admission_status_to = request.form.get("admission_status_to", response.admission_status_to)
    response.new_career = request.form.get("new_career", response.new_career)

    # Post-bac study objective checkboxes
    response.second_bachelor_plan = request.form.get("study_objective") == "second_degree"
    response.graduate_study_objective = request.form.get("study_objective") == "grad_study"
    response.teacher_certification = request.form.get("study_objective") == "teacher_cert"
    response.personal_enrichment_objective = request.form.get("study_objective") == "enrichment"

    response.program_change_from = request.form.get("program_change_from", response.program_change_from)
    response.program_change_to = request.form.get("program_change_to", response.program_change_to)
    response.plan_change_from = request.form.get("plan_change_from", response.plan_change_from)
    response.plan_change_to = request.form.get("plan_change_to", response.plan_change_to)
    response.degree_objective_change_from = request.form.get("degree_objective_change_from", response.degree_objective_change_from)
    response.degree_objective_change_to = request.form.get("degree_objective_change_to", response.degree_objective_change_to)

    response.requirement_term_catalog = request.form.get("requirement_term_catalog", response.requirement_term_catalog)
    response.requirement_term_program_plan = request.form.get("requirement_term_program_plan", response.requirement_term_program_plan)

    response.additional_plan_degree_type = request.form.get("additional_plan_degree_type", response.additional_plan_degree_type)
    response.additional_plan_degree_type_other = request.form.get("additional_plan_degree_type_other", response.additional_plan_degree_type_other)
    response.primary_plan = "primary_plan" in request.form
    response.secondary_plan = "secondary_plan" in request.form

    response.second_degree_type = request.form.get("second_degree_type", response.second_degree_type)
    response.minor_change_from = request.form.get("minor_change_from", response.minor_change_from)
    response.minor_change_to = request.form.get("minor_change_to", response.minor_change_to)
    response.additional_minor = request.form.get("additional_minor", response.additional_minor)

    # === Explanation and Signature ===
    response.explanation = request.form.get("explanation", response.explanation)
    response.student_signature = request.form.get("student_signature", response.student_signature)

    date_str = request.form.get("date")
    if date_str:
        try:
            response.signature_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass  # invalid date format

    response.date_submitted = datetime.utcnow()
    response.department_id =  3 
    response.approval_status = 1
    db.session.commit()


    return jsonify({"message": "Form progress saved successfully!"}), 200

@form_bp.route("/gen_cm_pdf", methods = ["POST"])
def gen_cm_pdf():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]

    response = GeneralPetition.query.filter_by(user_id=user_id, is_finalized=False).first()
    if not response:
        response = GeneralPetition(user_id=user_id)
        db.session.add(response)
        #---------- This part down is for building the PDF (Alex can you work on this) ----------

    coord_map = {#(x goes down, y goes to left)
    # --- Student Info ---
    "student_first_name": (73.75, 600.00),
    "student_last_name": (73.00, 750.00),
    "student_middle_name": (73.00, 475.00),
    "student_uh_id": (92.30, 705.00),
    "student_phone_number": (92.30, 550.00),
    "student_mailing_address": (113.00, 710.00),
    "student_city": (133.00, 760.00),
    "student_state": (133.00, 635.00),
    "student_zip_code": (133.00, 550.00),
    "student_email": (133.00, 460.00),

    #advisor commented out until implementation
    #"current_program": (78.50, 280.00), 
    #"current_plan": (78.50, 150.00),
    #"petition_effective_before_class_day": (112.90, 240.00),
    #"petition_effective_after_class_day": (134, 240),

    # --- Petition purpose (sample) ---
    "program_status_action": (196.00, 710.00),

    # --- New blanks from image, labeled a1 to a50 ---
    "plan_change_from": (195.80, 540.08),
    "plan_change_to": (195.80, 470.09),
    "second_degree_type": (195.80, 275.61),
    "second_degree_type_other": (195.80, 140.61),
    "admission_status_from": (216.50, 646.86),
    "admission_status_to": (216.50, 600.86),
    "degree_objective_change_from": (216.50, 487.31),
    "degree_objective_change_to": (216.50, 403.75),
    "minor_change_from": (216.50, 280.13),
    "minor_change_to": (216.50, 145.21),
    "new_career": (236.06, 675.25),
    "additional_minor": (236.06, 160.76),
    "requirement_term_catalog": (277.46, 468.99),
    "requirement_term_program_plan": (277.46, 365.40),
    "additional_plan_degree_type": (298.16, 535.68),
    "additional_plan_degree_type_other": (298.16, 405.42),
    "program_change_from": (318.86, 770.27),
    "program_change_to": (318.86, 698.25),
    "explanation_of_request": (361.57, 750.25),



    #---to be implemented---
    #"advisor_comments": (470.59, 260.37),
    #"advisor_signature": (447.63, 570.95),
    #"advisor_printed_name": (447.63, 471.01),
    #"advisor_signature_date": (447.63, 361.11),
    #"chair_signature": (478.70, 578.95),
    #"chair_printed_name": (478.70, 471.01),
    #"chair_signature_date": (478.70, 361.11),


    #check boxes remember to implement if X make font bigger
    "Q1":(187, 779),
    "Q2":(217, 779),
    "Q3":(238, 779),
    "Q4":(310, 779),
    "Q5":(187, 546),
    "Q6":(207, 546), 
    "Q7":(269, 546), 
    "Q8":(289, 546),
    "Q9":(187, 290),
    "Q10":(207, 290),
    "Q11":(237, 290),
    "Q12":(247, 290),
    "Q13":(257, 290),
    "Q14":(280, 290),
    "Q15":(304, 290),
    "Q16":(319, 290),
    "Q17":(333, 290),

}
    #------ below os for oprinting pdf ----


    doc = fitz.open("static/emptyforms/CM.pdf") # open pdf

    # Choose the page to write on (0-indexed)
    page = doc.load_page(0)  # For the first page

    # Define text style (font, size, color, etc.)
    font = "helv"  # Use font name as string (e.g., 'helv' for Helvetica)
    size = 12  # Font size
    color = (0, 0, 0)  # Black color in RGB (0, 0, 0)

     # If the field exists (is not None), insert the value into the PDF
    # Iterate through the student_map
    # Iterate through the student_map
    for field, position in coord_map.items():
        # Get the field value from the response object
        field_value = getattr(response, field, None)

    # Prevent errors by ensuring initials exist before accessing
        #print("FIELD: ", field, " FIELD_VALIE: ", field_value)
        if isinstance(field_value, bool):  # If the value is a boolean
            print("FIELD: ", field, " FIeld Value: ", field_value)
            if field_value:  # If True,
                page.insert_text(position, "x", fontname=font, fontsize=size, color=color, rotate=90)
            else:  # If False, output nothing
                page.insert_text(position, " ", fontname=font, fontsize=size, color=color, rotate=90)
        elif isinstance(field_value, (str, int)):  # If the value is a string or integer
            if field_value:  # If the string or integer is not empty
                #print("FIELD: ", field, " FIELD_VALUE: ", field_value)
                page.insert_text(position, str(field_value), fontname=font, fontsize=size, color=color, rotate=90)
            else:  # If the string is empty, output nothing
                page.insert_text(position, " ", fontname=font, fontsize=size, color=color, rotate=90)

    # Handle other cases if needed
    else:
        page.insert_text(position, " ", fontname=font, fontsize=size, color=color, rotate=90)

    #"student_signature": (100, 738)
    current_date = datetime.utcnow().strftime("%m/%d/%Y")
    # Insert the formatted date into the PDF
    page.insert_text((405.48, 400.08), current_date, fontname=font, fontsize=size, color=color, rotate=90)

    #this sets up signature filename
    filename = f"{user_id}.jpg"
    filename = secure_filename(filename)

    # Save the file
    file_path = os.path.join("static/signatures", filename)

    # List all files in the SIGNATURE_UPLOAD_FOLDER
        # Position for student signature
    student_signature_position = (343.48, 579.31)  # The coordinates (x, y) where the signature will be inserted
    # Insert Student Signature (JPG image)
    try:
        img_rect = fitz.Rect(student_signature_position[0], student_signature_position[1], 
                            student_signature_position[0] + 100, student_signature_position[1] + 50)  # Adjust size if needed
        page.insert_image(img_rect, filename = file_path, rotate=90)
        #print("SUCCESS")
    except Exception as e:
        print(f"Error inserting student signature: {e}")

    user=session["user"]

    # Avoid accessing first[0] or last[0] if empty
    filename = f"{user_id}.pdf"
    filename = secure_filename(filename)

    # Define the path where the document should be saved
    save_path = os.path.join('static', 'documents', 'CM', filename)

    # Save the document (assuming 'doc' is a document object with a 'save' method)
    doc.save(save_path)

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
        response.approval_status = 1
        db.session.add(response)
        db.session.commit()

        # If finalized, remove any unfinished drafts
        if is_finalized:
            # 1️⃣  Delete every other GeneralPetition from *this* user
            (db.session.query(TWResponses)
                .filter(
                    TWResponses.user_id == user_id,
                    TWResponses.id != response.id        # keep the one we just saved
                )
                .delete(synchronize_session="fetch")         # or "False" for speed
            )

            # Mark this response as “submitted / pending approval”
            response.approval_status = 2   # 2 = submitted, waiting for approver
            db.session.add(response)
            db.session.commit()
            flash("Form submitted successfully!", "success")
            
            approval = ApprovalProcess(
                user_id=response.user_id,
                approver_id=user_exists.id,  # whoever is submitting it
                form_type = 2,
                status="pending",
                decision_date=datetime.utcnow(),
                comments=None,
            )
            db.session.add(approval)
            db.session.commit()

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
    response.approval_status = 1
    db.session.commit()

    gen_tw_pdf()

    return jsonify({"message": "Form progress saved successfully!"}), 200

@form_bp.route("/gen_tw_pdf", methods = ["POST"])
def gen_tw_pdf():
 #---------- This part down is for building the PDF ----------
    """Saves the current form progress asynchronously."""
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]

    # Check for existing draft
    response = TWResponses.query.filter_by(user_id=user_id, is_finalized=False).first()
    
    if not response:
        response = TWResponses(user_id=user_id)
        db.session.add(response)
    # Ensure the student_name is not None and has at least one name
    name_parts = (response.student_name or "").strip().split()

    # Assign default empty values if any name part is missing
    first = name_parts[0] if len(name_parts) > 0 else ""
    middle = name_parts[1] if len(name_parts) > 1 else ""
    last = name_parts[2] if len(name_parts) > 2 else ""



    try:
        doc = fitz.open("static/emptyforms/TW.pdf")  # open pdf
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

        # 6) Check if form is finalized
        is_finalized = "confirm_acknowledgment" in request.form
        response.is_finalized = is_finalized
        response.last_updated = datetime.utcnow()

        response.department_id = "2"
        response.approval_status = 1
        db.session.add(response)
        db.session.commit()

        # If user finalized the form, remove other drafts
        if is_finalized:
            # 1️⃣  Delete every other RCLResponses from *this* user
            (db.session.query(RCLResponses)
                .filter(
                    RCLResponses.user_id == user_id,
                    RCLResponses.id != response.id        # keep the one we just saved
                )
                .delete(synchronize_session="fetch")         # or "False" for speed
            )

            # Mark this response as “submitted / pending approval”
            response.approval_status = 2   # 2 = submitted, waiting for approver
            db.session.add(response)
            db.session.commit()
            flash("RCL Form submitted successfully!", "success")
            # Create ApprovalProcess entry
            approval = ApprovalProcess(
                user_id=response.user_id,
                approver_id=user_exists.id,  # whoever is submitting it
                form_type = 2,
                status="pending",
                decision_date=datetime.utcnow(),
                comments=None,
            )
            db.session.add(approval)
            db.session.commit()
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


    print(request.form) #testing

    if not response:
        response = RCLResponses(user_id=user_id)
        db.session.add(response)

    # Parse main_option
    main_option = request.form.get("main_option", "")
    print("This is the main option: " + main_option)  

    option_map = { #working as should
        "IAI": "initial_adjustment_issues",
        "ICLP": "improper_course_level_placement",
        "Medical Reason": "medical_reason",
        "Final Semester": "final_semester",
        "Concurrent Enrollment": "concurrent_enrollment",
    }

    # Reset all to False first
    for attr in option_map.values():
        setattr(response, attr, False)

    # Set the selected one to True
    if main_option in option_map:
        setattr(response, option_map[main_option], True)


    # IAI suboptions
    if response.initial_adjustment_issues: #working as it should
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
    response.dclass1 = request.form.get("course1", "").strip()
    response.dclass2 = request.form.get("course2", "").strip()
    response.dclass3 = request.form.get("course3", "").strip()

    # total_hours => stored in remaining_hours_uh
    total_hrs = request.form.get("total_hours", "0")
    response.remaining_hours_uh = int(total_hrs) if total_hrs.isdigit() else None

    # year_hours
    year_hours_str = request.form.get("year_hours", "0")
    # e.g. response.year_hours = int(year_hours_str) if year_hours_str.isdigit() else None

    # last updated
    response.last_updated = datetime.utcnow()
    response.department_id = "2"
    response.approval_status = 1
    db.session.commit()

    gen_rcl_pdf()

    return jsonify({"message": "Form progress saved successfully!"}), 200

@form_bp.route("/gen_rcl_pdf", methods=["POST"])
def gen_rcl_pdf():
    print("RCL GEN")
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]
    response = RCLResponses.query.filter_by(user_id=user_id, is_finalized=False).first()
    print("THIS IS THE RESPONSE: ", response)

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

    doc = fitz.open("static/emptyforms/RCL.pdf") # open pdf

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
                print("FIELD: ", field, " FIELD_VALUE: ", field_value)
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

@form_bp.route("/preview_form", methods=["POST"])
def preview_form():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]
    form_type = request.form.get("form_type")  # Get the form type (TW or RCL)

    # Validate form type
    if form_type not in ["TW", "RCL", "CM"]:
        return jsonify({"error": "Invalid form type"}), 400

    # Call the appropriate save function
    if form_type == "TW":
        print("TEST1")
        save_tw_progress()
        gen_tw_pdf()
    elif form_type == "RCL":
        print("TEST2")
        save_rcl_progress()
        gen_rcl_pdf()
    elif form_type == "CM":
        print("TEST3")
        
        save_rcl_progress()

        gen_cm_pdf()


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
    
@form_bp.route("/save_ca_progress", methods=["POST"])
def save_ca_progress():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]

    # get current draft or start a new one
    response = CAResponses.query.filter_by(user_id=user_id, is_finalized=False).first()
    if not response:
        response = CAResponses(user_id=user_id)
        db.session.add(response)

    # -------- populate / update -----------
    response.user_name           = request.form.get("user_name", response.user_name)
    response.user_phone          = request.form.get("user_phone", response.user_phone)
    response.user_email          = request.form.get("user_email", response.user_email)
    response.comments            = request.form.get("comments", response.comments)
    response.complete_dept_name  = request.form.get("complete_dept_name", response.complete_dept_name)
    response.college_or_division = request.form.get("college_or_division", response.college_or_division)
    response.dept_acronym        = request.form.get("dept_acronym", response.dept_acronym)
    response.building_location   = request.form.get("building_location", response.building_location)

    date_str = request.form.get("date")
    if date_str:
        try:
            response.signature_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            pass

    # -------- bookkeeping -----------
    response.last_updated  = datetime.utcnow()
    response.department_id = 4
    response.approval_status = 1           # draft
    db.session.commit()

    return jsonify({"message": "Form progress saved successfully!"}), 200


# -------------------------- 2)  full form view / submit ----------------------
@form_bp.route("/ca_form", methods=['GET', 'POST'])
def fill_ca_form():
    if "user" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    user_id = session["user"]["id"]
    existing_response = CAResponses.query.filter_by(
        user_id=user_id, is_finalized=False
    ).first()

    # ---------------- POST ---------------------------------------------------
    if request.method == 'POST':
        response = existing_response if existing_response else CAResponses(user_id=user_id)

        # ① populate fields
        response.user_name           = request.form.get("user_name", "").strip()
        response.user_phone          = request.form.get("user_phone", "").strip()
        response.user_email          = request.form.get("user_email", "").strip()
        response.comments            = request.form.get("comments", "").strip()
        response.complete_dept_name  = request.form.get("complete_dept_name", "").strip()
        response.college_or_division = request.form.get("college_or_division", "").strip()
        response.dept_acronym        = request.form.get("dept_acronym", "").strip()
        response.building_location   = request.form.get("building_location", "").strip()

        # ② bookkeeping
        response.last_updated  = datetime.utcnow()
        response.department_id = 4
        response.approval_status = 1

        # ③ did the user finalize?
        is_finalized = "confirm_acknowledgment" in request.form
        response.is_finalized = is_finalized

        db.session.add(response)
        db.session.commit()                # guarantees response.id exists

        # ④ finalize branch ---------------------------------------------------
        if is_finalized:
            # delete ALL other CA drafts / old submissions from the same user
            (db.session.query(CAResponses)
               .filter(
                   CAResponses.user_id == user_id,
                   CAResponses.id != response.id
               )
               .delete(synchronize_session="fetch")
            )

            # mark this one as submitted / pending approval
            response.approval_status = 2
            db.session.add(response)
            db.session.commit()

            # create ApprovalProcess row
            approval = ApprovalProcess(
                user_id    = response.user_id,
                approver_id= session["user"]["id"],    # who pressed submit
                form_type  = 4,                        # CA form
                status     = "pending",
                decision_date = datetime.utcnow()
            )
            db.session.add(approval)
            db.session.commit()

            flash("Form submitted successfully!", "success")
            return redirect(url_for("dashboard"))

        # ⑤ draft branch ------------------------------------------------------
        flash("Form saved successfully!", "success")
        return redirect(url_for("form.fill_ca_form"))

    # ---------------- GET ----------------------------------------------------
    return render_template("ca_form.html", response=existing_response)

@form_bp.route("/gen_ca_pdf", methods = ["POST"])
def gen_ca_pdf():
    if "user" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user"]["id"]

    response = CAResponses.query.filter_by(user_id=user_id, is_finalized=False).first()
    if not response:
        response = CAResponses(user_id=user_id)
        db.session.add(response)
        #---------- This part down is for building the PDF (Alex can you work on this) ----------
    first_name, last_name = response.user_name.strip().split(" ", 1)
    
    coord_map = {#(x goes down, y goes to left)
    # --- Student Info ---
    "complete_dept_name": (201.79917907714844, 127.67596435546875),
    "college_or_division": (265.581298828125, 160.074462890625),
    "dept_acronym": (203.28892517089844, 192.47296142578125),
    "opening_date": (244.5893096923828, 224.8714599609375),
    "building_location": (292.6187744140625, 257.26995849609375),
    "user_phone": (111.02850341796875, 414.86395263671875),
    "user_email": (105.75000762939453, 447.262451171875),
    "comments": (174.7755126953125, 479.66094970703125)
}
    doc = fitz.open("static/emptyforms/CA.pdf") # open pdf

    # Choose the page to write on (0-indexed)
    page = doc.load_page(0)  # For the first page

    # Define text style (font, size, color, etc.)
    font = "helv"  # Use font name as string (e.g., 'helv' for Helvetica)
    size = 12  # Font size
    color = (0, 0, 0)  # Black color in RGB (0, 0, 0)

     # If the field exists (is not None), insert the value into the PDF
    # Iterate through the student_map
    # Iterate through the student_map
    for field, position in coord_map.items():
        # Get the field value from the response object
        field_value = getattr(response, field, None)
        page.insert_text(position, str(field_value), fontname=font, fontsize=size, color=color)

    #"student_signature": (100, 738)
    current_date = datetime.utcnow().strftime("%m/%d/%Y")
    # Insert the formatted date into the PDF
    page.insert_text((137.9971923828125, 350.06695556640625), str(first_name, fontname=font, fontsize=size, color=color))
    page.insert_text((137.2720947265625, 382.4654541015625), str(last_name, fontname=font, fontsize=size, color=color))
                     

    #this sets up signature filename

    # Avoid accessing first[0] or last[0] if empty
    filename = f"{user_id}.pdf"
    filename = secure_filename(filename)

    # Define the path where the document should be saved
    save_path = os.path.join('static', 'documents', 'CA', filename)

    # Save the document (assuming 'doc' is a document object with a 'save' method)
    doc.save(save_path)


@form_bp.route("/view_pdf/<int:dept_id>/<int:user_id>")
def view_pdf(dept_id, user_id):
    """Find and display the latest generated PDF for a request."""

    # Map department IDs to form models and labels
    DEPT_MODEL_MAP = {
        1: (TWResponses, "TW"),
        2: (RCLResponses, "RCL"),
        3: (GeneralPetition, "CM"),
        4: (CAResponses, "CA")
    }

    model_info = DEPT_MODEL_MAP.get(dept_id)

    if not model_info:
        flash("Invalid department ID.", "warning")
        return redirect(url_for("admin.admindashboard"))

    model, form_type = model_info


    # Construct the path to the PDF
    filename = f"{user_id}.pdf"
    pdf_path = os.path.join("static", "documents", form_type, filename)
    print("TEST PDF PATH:", pdf_path)

    # Check if the file exists
    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype="application/pdf")

    flash("PDF not found!", "warning")
    return redirect(url_for("admin.admindashboard"))


@form_bp.route("/download_pdf/<int:dept_id>/<int:user_id>")
def download_pdf(dept_id, user_id):
 # Map department IDs to form models and labels
    DEPT_MODEL_MAP = {
        1: (TWResponses, "TW"),
        2: (RCLResponses, "RCL"),
        3: (GeneralPetition, "CM"),
        4: (CAResponses, "CA")
    }

    model_info = DEPT_MODEL_MAP.get(dept_id)

    if not model_info:
        flash("Invalid department ID.", "warning")
        return redirect(url_for("admin.admindashboard"))

    model, form_type = model_info


    # Construct the path to the PDF
    filename = f"{user_id}.pdf"
    pdf_path = os.path.join("static", "documents", form_type, filename)
    print("TEST PDF PATH:", pdf_path)

    # Check if the file exists
    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype="application/pdf")


    if os.path.exists(pdf_path):
        return send_file(pdf_path, mimetype="application/pdf", as_attachment=True)

    flash("PDF not found!", "warning")
    return redirect(url_for("admin.admindashboard"))