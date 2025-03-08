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
    approvals = db.relationship("ApprovalProcess", back_populates="approver")
    #store the signature file path
    signature_path = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def __repr__(self):
        return f"<User {self.name} - Role: {self.role.name if self.role else 'None'}> - Status: {self.status.name if self.status else 'None'}>"
    
class Request(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # "RCL" or "TW"
    semester = db.Column(db.String(20), nullable=True)  # Optional fields depending on type
    year = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)  # Stores extra info like dropped courses
    status = db.Column(db.String(50), default="draft")  # draft, pending, approved, rejected
    pdf_path = db.Column(db.String(255))  # Stores the generated PDF path

    approval_process = db.relationship("ApprovalProcess", back_populates="request", cascade="all, delete-orphan")

class ApprovalProcess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, approved, rejected
    decision_date = db.Column(db.DateTime)  # Timestamp of approval/rejection
    comments = db.Column(db.Text)  # Any comments from the approver
    signature_path = db.Column(db.String(255))  # Path to the approver's signature

    request = db.relationship("Request", back_populates="approval_process")
    approver = db.relationship("User", back_populates="approvals")