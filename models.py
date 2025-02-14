from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Role Table
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'administrator', 'basicuser',
    
    def __repr__(self):
        return f"<Role {self.name}>"

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    microsoft_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    profile_picture = db.Column(db.String(200))  # Optional field

    # Foreign Key to Role Table
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    def __repr__(self):
        return f"<User {self.name} - Role: {self.role.name if self.role else 'None'}>"
