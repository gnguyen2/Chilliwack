from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

# Role Table
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'administrator', 'basicuser',
    
    def __repr__(self):
        return f"<{self.name}>"
    
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

    # Foreign Key to Role Table
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    # Foreign Key to Status Table
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))
    status = db.relationship('Status', backref=db.backref('users', lazy=True))

    #establish a relationship with ApprovalProcess
    approvals = db.relationship("ApprovalProcess", back_populates="approver", lazy=True)
    #store the signature file path
    signature_path = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __repr__(self):
        return f"<User {self.name} - Role: {self.role.name if self.role else 'None'}> - Status: {self.status.name if self.status else 'None'}>"
    
class Request(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    student_email = db.Column(db.String(100), db.ForeignKey('user.email'), nullable=True)
    request_type = db.Column(db.String(50), nullable=False)  # "RCL" or "TW"
    semester = db.Column(db.String(20), nullable=True)  # Optional fields depending on type
    year = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)  # Stores extra info like dropped courses
    status = db.Column(db.String(50), default="draft")  # draft, pending, approved, rejected
    pdf_path = db.Column(db.String(255))  # Stores the generated PDF path

    approvals = db.relationship("ApprovalProcess", back_populates="request", cascade="all, delete-orphan")

class ApprovalProcess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, approved, rejected
    decision_date = db.Column(db.DateTime)  # Timestamp of approval/rejection
    comments = db.Column(db.Text)  # Any comments from the approver
    signature_path = db.Column(db.String(255))  # Path to the approver's signature

    # Relationships
    request = db.relationship("Request", back_populates="approvals")
    approver = db.relationship("User", foreign_keys=[approver_id], back_populates="approvals")

    def __repr__(self):
        return f"<Approval {self.id} - Request: {self.request_id} - Status: {self.status}>"
    
class RCLResponses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", backref="responses")

    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=True)  # Nullable for drafts
    request = db.relationship("Request", backref="form_responses")

    # Student Information
    student_name = db.Column(db.String(100), nullable=True)
    ps_id = db.Column(db.String(20), nullable=True)
    student_signature = db.Column(db.String(255), nullable=True)  # Path to signature file
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Type of Reduced Course Load
    academic_difficulty = db.Column(db.Boolean, default=False)
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
    concurrent_proof_attached = db.Column(db.Boolean, default=False)

    # Semester Information
    semester_fall = db.Column(db.Boolean, default=False)
    semester_spring = db.Column(db.Boolean, default=False)
    drop_courses = db.Column(db.String(255), nullable=True)  # Store comma-separated course numbers
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
    
class TWResponses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", backref="withdrawal_responses")

    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=True)  # Nullable for drafts
    request = db.relationship("Request", backref="withdrawal_responses")

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

    # Approval Signatures
    financial_aid_signature = db.Column(db.String(255), nullable=True)  # Path to Financial Aid signature file
    financial_aid_date = db.Column(db.DateTime, nullable=True)

    isss_signature = db.Column(db.String(255), nullable=True)  # Path to ISSSO signature file
    isss_date = db.Column(db.DateTime, nullable=True)

    athletics_signature = db.Column(db.String(255), nullable=True)  # Path to Athletics signature file
    athletics_date = db.Column(db.DateTime, nullable=True)

    veterans_signature = db.Column(db.String(255), nullable=True)  # Path to Veterans' Office signature file
    veterans_date = db.Column(db.DateTime, nullable=True)

    advisor_name = db.Column(db.String(100), nullable=True)
    advisor_signature = db.Column(db.String(255), nullable=True)  # Path to Advisor signature file
    advisor_date = db.Column(db.DateTime, nullable=True)

    # Status Tracking
    is_finalized = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)