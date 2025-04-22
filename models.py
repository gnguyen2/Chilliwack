from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

# Role Table
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'administrator', 'basicuser',
    
    def __repr__(self):
        return f"<{self.name}>"

# For departments
class Department(db.Model):
    __tablename__ = 'department'
    id = db.Column(db.Integer, primary_key=True)
    # 0 = admin, 1 = TW, 2 = RCL, 3 = genpet, 4 = address
    name = db.Column(db.String(100), unique=True, nullable=False)

# Status Table
class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'active', 'deactivated',
    
    def __repr__(self):
        return f"<{self.name}>"
       
# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    microsoft_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    # Foreign Key to Role Table
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    # Foreign Key to Status Table
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))
    status = db.relationship('Status', backref=db.backref('users', lazy=True))

    #establish a relationship with ApprovalProcess
    approvals = db.relationship("ApprovalProcess", back_populates="approver", foreign_keys="ApprovalProcess.approver_id", lazy=True)
    #store the signature file path
    signature_path = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __repr__(self):
        return f"<User {self.name} - Role: {self.role.name if self.role else 'None'}> - Status: {self.status.name if self.status else 'None'}>"


# delegation table
class Delegation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_parent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    to_child_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    dept_from = db.Column(db.Integer, db.ForeignKey('department.id'))
    dept_to = db.Column(db.Integer, db.ForeignKey('department.id')) 
    date = db.Column (db.DateTime)

class ApprovalProcess(db.Model):
    req_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False) #This will be the ID of the requesting student
    form_type = db.Column(db.Integer, db.ForeignKey('department.id'), nullable = False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, approved, rejected
    decision_date = db.Column(db.DateTime)  # Timestamp of approval/rejection
    comments = db.Column(db.Text)  # Any comments from the approver
    signature_path = db.Column(db.String(255))  # Path to the approver's signature

    # Relationships
    approver = db.relationship("User", foreign_keys=[approver_id], back_populates="approvals")

    def __repr__(self):
        return f"<Approval {self.id} - Request: {self.req_id} - Status: {self.status}>"

class CAResponses(db.Model):
    __tablename__ = 'ca_responses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    user_id = db.Column(db.Integer, nullable = False)
    user_name = db.Column(db.String(255), nullable = False)
    user_phone = db.Column(db.String(255), nullable = False)
    user_email = db.Column(db.String(255), nullable = False)
    comments = db.Column (db.Text, nullable = True)

    # 1 = in prog, 2 = finalizad awaiting approval, 3=approved
    approval_status = db.Column(db.Integer, server_default="1")

    complete_dept_name = db.Column(db.String(255), nullable=False)
    college_or_division = db.Column(db.String(255), nullable=False)
    dept_acronym = db.Column(db.String(50), nullable=True)
    opening_date = db.Column(db.String(50), nullable=True)
    building_location = db.Column(db.String(255), nullable=True)

    is_finalized = db.Column(db.Boolean, default=False)

class RCLResponses(db.Model):
    __tablename__ = "rcl_responses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", backref="responses")
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    # 1 = in prog, 2 = finalizad awaiting approval, 3=approved
    approval_status = db.Column(db.Integer, server_default="1")

    # Student Information
    student_name = db.Column(db.String(100), nullable=True)
    ps_id = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    student_signature = db.Column(db.String(255), nullable=True)  # Path to signature file
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Type of Reduced Course Load
    initial_adjustment_issues = db.Column(db.Boolean, default=False)
    initial_adjustment_explanation = db.Column(db.Text, nullable=True)

    improper_course_level_placement = db.Column(db.Boolean, default=False)
    iclp_class1 = db.Column(db.String(50), nullable=True)
    iclp_professor1 = db.Column(db.String(100), nullable=True)
    iclp_professor_signature1 = db.Column(db.String(255), nullable=True)  # Path to professor signature file
    iclp_date1 = db.Column(db.DateTime, nullable=True)

    iclp_class2 = db.Column(db.String(50), nullable=True)
    iclp_professor2 = db.Column(db.String(100), nullable=True)
    iclp_professor_signature2 = db.Column(db.String(255), nullable=True)  # Path to professor signature file
    iclp_date2 = db.Column(db.DateTime, nullable=True)

    # Medical Reason
    medical_reason = db.Column(db.Boolean, default=False)
    medical_letter_attached = db.Column(db.Boolean, default=False)

    # Final Semester
    final_semester = db.Column(db.Boolean, default=False)
    final_semester_hours_needed = db.Column(db.Integer, nullable=True)

    # Concurrent Enrollment
    concurrent_enrollment = db.Column(db.Boolean, default=False)
    concurrent_university_name = db.Column(db.String(100), nullable=True)
    concurrent_hours_uh = db.Column(db.Integer, nullable=True)
    concurrent_hours_other = db.Column(db.Integer, nullable=True)

    # Semester Information
    semester_fall = db.Column(db.Boolean, default=False)
    semester_spring = db.Column(db.Boolean, default=False)
    year_last_digit = db.Column(db.Integer, default=False)
    dclass1 = db.Column(db.String(255), nullable=True)  # Store comma-separated course numbers
    dclass2 = db.Column(db.String(255), nullable=True)
    dclass3 = db.Column(db.String(255), nullable=True)
    remaining_hours_uh = db.Column(db.Integer, nullable=True)

    # Approval Signatures
    advisor_name = db.Column(db.String(100), nullable=True)
    advisor_signature = db.Column(db.String(255), nullable=True)  # Path to signature file
    advisor_date = db.Column(db.DateTime, nullable=True)

    isss_signature = db.Column(db.String(255), nullable=True)  # Path to ISSSO signature file
    isss_date = db.Column(db.DateTime, nullable=True)

    # Track whether the form is finalized or still in progress
    is_finalized = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add a relationship for multiple documents
    documents = db.relationship("RCLDocuments", back_populates="response", cascade="all, delete-orphan")

class RCLDocuments(db.Model):
    __tablename__ = "rcl_documents"

    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("rcl_responses.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    

    # Relationship back to RCLResponses
    response = db.relationship("RCLResponses", back_populates="documents")

    def __repr__(self):
        return f"<RCLDocuments {self.id} - {self.file_name}>"

class TWResponses(db.Model):
    __tablename__ = "tw_responses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", backref="withdrawal_responses")

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    # 1 = in prog, 2 = finalizad awaiting approval, 3=approved
    approval_status = db.Column(db.Integer, server_default="1")

    # Student Information
    student_name = db.Column(db.String(100), nullable=True)
    ps_id = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    program = db.Column(db.String(100), nullable=True)
    academic_career = db.Column(db.String(100), nullable=True)
    student_signature = db.Column(db.String(255), nullable=True)  # Path to signature file
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Withdrawal Term
    withdrawal_term_fall = db.Column(db.Boolean, default=False)
    withdrawal_term_spring = db.Column(db.Boolean, default=False)
    withdrawal_term_summer = db.Column(db.Boolean, default=False)
    withdrawal_year = db.Column(db.Integer, nullable=True)

    # Initial Acknowledgments
    financial_aid_ack = db.Column(db.Boolean, default=False)
    international_students_ack = db.Column(db.Boolean, default=False)
    student_athlete_ack = db.Column(db.Boolean, default=False)
    veterans_ack = db.Column(db.Boolean, default=False)
    graduate_students_ack = db.Column(db.Boolean, default=False)
    doctoral_students_ack = db.Column(db.Boolean, default=False)
    housing_ack = db.Column(db.Boolean, default=False)
    dining_ack = db.Column(db.Boolean, default=False)
    parking_ack = db.Column(db.Boolean, default=False)

    # Supporting Documents
    supporting_documents_attached = db.Column(db.Boolean, default=False)
    supporting_document_path = db.Column(db.String(255), nullable=True)  # Path to uploaded documents

    # Status Tracking
    is_finalized = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add a relationship to store multiple documents
    documents = db.relationship("TWDocuments", back_populates="response", cascade="all, delete-orphan")

class TWDocuments(db.Model):
    __tablename__ = "tw_documents"

    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("tw_responses.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship back to TWResponses
    response = db.relationship("TWResponses", back_populates="documents")

    def __repr__(self):
        return f"<TWDocuments {self.id} - {self.file_name}>"

class GeneralPetition(db.Model):  # FOR INTEGRATION
    __tablename__ = 'general_petition'
    
    # Primary Key (Django automatically adds an id field if not specified)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship("User", backref="gen_pet_responses")

    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)

    # 1 = in prog, 2 = finalizad awaiting approval, 3=approved
    approval_status = db.Column(db.Integer, server_default="1")

    # Student Information Section
    student_last_name = db.Column(db.String(100), nullable=True)
    student_first_name = db.Column(db.String(100), nullable=True)
    student_middle_name = db.Column(db.String(100), nullable=True)
    student_uh_id = db.Column(db.String(20), nullable=True)
    student_phone_number = db.Column(db.String(20), nullable=True)
    student_program_plan = db.Column(db.String(100), nullable=True)
    student_academic_career = db.Column(db.String(100), nullable=True)
    student_mailing_address = db.Column(db.Text, nullable=True)
    student_city = db.Column(db.String(100), nullable=True)
    student_state = db.Column(db.String(50), nullable=True)
    student_zip_code = db.Column(db.String(10), nullable=True)
    student_email = db.Column(db.String(255), nullable=True)  # Email can be stored as String

    # Petition Purpose Details
    program_status_action = db.Column(db.String(100), nullable=True)
    admission_status_from = db.Column(db.String(100), nullable=True)
    admission_status_to = db.Column(db.String(100), nullable=True)
    new_career = db.Column(db.String(100), nullable=True)
    post_bac_study_objective = db.Column(db.String(100), nullable=True)
    second_bachelor_plan = db.Column(db.Boolean, default=False)
    graduate_study_objective = db.Column(db.Boolean, default=False)
    teacher_certification = db.Column(db.Boolean, default=False)
    personal_enrichment_objective = db.Column(db.Boolean, default=False)

    program_change_from = db.Column(db.String(100), nullable=True)
    program_change_to = db.Column(db.String(100), nullable=True)

    plan_change_from = db.Column(db.String(100), nullable=True)
    plan_change_to = db.Column(db.String(100), nullable=True)

    degree_objective_change_from = db.Column(db.String(100), nullable=True)
    degree_objective_change_to = db.Column(db.String(100), nullable=True)

    requirement_term_catalog = db.Column(db.String(100), nullable=True) #theres only one input box?
    requirement_term_career = db.Column(db.String(100), nullable=True)
    requirement_term_program_plan = db.Column(db.String(100), nullable=True)

    additional_plan_degree_type = db.Column(db.String(50), nullable=True)
    additional_plan_degree_type_other = db.Column(db.String(100), nullable=True)
    primary_plan = db.Column(db.Boolean, default=False)
    secondary_plan = db.Column(db.Boolean, default=False)

    second_degree_type = db.Column(db.String(100), nullable=True)

    minor_change_from = db.Column(db.String(100), nullable=True)
    minor_change_to = db.Column(db.String(100), nullable=True)
    additional_minor = db.Column(db.String(100), nullable=True)

    #imo these are not needed - calvin
    degree_requirement_exception_details = db.Column(db.Text, nullable=True)
    special_problems_course_list = db.Column(db.Text, nullable=True)

    course_overload_gpa = db.Column(db.String(10), nullable=True)
    course_overload_credit_hours = db.Column(db.String(10), nullable=True)
    course_overload_course_list = db.Column(db.Text, nullable=True)

    graduate_leave_of_absence_request_details = db.Column(db.Text, nullable=True)
    graduate_reinstatement_request_details = db.Column(db.Text, nullable=True)
    other_request_details = db.Column(db.Text, nullable=True)

    explanation_of_request = db.Column(db.Text, nullable=True)
    
    #could all be put into this column
    explanation = db.Column(db.Text, nullable=True)

    # In Django, ImageField is used for file uploads; in SQLAlchemy, store the path or use a BLOB.
    # For simplicity, store the path as a db.String here:
    student_signature = db.Column(db.String, nullable=True)

    signature_date = db.Column(db.Date, nullable=True)

    # Checkbox Fields for Q1–Q17
    Q1 = db.Column(db.Boolean, default=False)
    Q2 = db.Column(db.Boolean, default=False)
    Q3 = db.Column(db.Boolean, default=False)
    Q4 = db.Column(db.Boolean, default=False) 
    Q5 = db.Column(db.Boolean, default=False)
    Q6 = db.Column(db.Boolean, default=False)
    Q7 = db.Column(db.Boolean, default=False)
    Q8 = db.Column(db.Boolean, default=False)
    Q9 = db.Column(db.Boolean, default=False)
    Q10 = db.Column(db.Boolean, default=False)
    Q11 = db.Column(db.Boolean, default=False)
    Q12 = db.Column(db.Boolean, default=False)
    Q13 = db.Column(db.Boolean, default=False)
    Q14 = db.Column(db.Boolean, default=False)
    Q15 = db.Column(db.Boolean, default=False)
    Q16 = db.Column(db.Boolean, default=False)
    Q17 = db.Column(db.Boolean, default=False)

    # Status Tracking
    is_finalized = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

    # Add a relationship to store multiple documents
    documents = db.relationship("GeneralPetitionDocuments", back_populates="response", cascade="all, delete-orphan")

class GeneralPetitionDocuments(db.Model):
    __tablename__ = "gen_pet_documents"

    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("general_petition.id"), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship back to TWResponses
    response = db.relationship("GeneralPetition", back_populates="documents")

    def __repr__(self):
        return f"<TWDocuments {self.id} - {self.file_name}>"