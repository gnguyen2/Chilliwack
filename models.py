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
    student = db.relationship("User", backref="requests")

    status = db.Column(db.String(50), default="draft")  # draft, submitted, returned, approved, rejected
    pdf_path = db.Column(db.String(255), nullable=True)  # Stores the generated PDF path

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to ApprovalProcess, tracks approvals history
    approvals = db.relationship("ApprovalProcess", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Request {self.id} - Student: {self.student.name} - Status: {self.status}>"

class ApprovalProcess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    request = db.relationship("Request", back_populates="approvals")

    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable, any admin can approve
    approver = db.relationship("User", back_populates="approvals")

    status = db.Column(db.String(50), default="pending")  # pending, approved, rejected
    decision_date = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of approval/rejection
    comments = db.Column(db.Text, nullable=True)  # Any comments from the approver
    signature_path = db.Column(db.String(255), nullable=True)  # Path to the approver's signature

    def __repr__(self):
        return f"<Approval {self.id} - Request: {self.request_id} - Status: {self.status}>"