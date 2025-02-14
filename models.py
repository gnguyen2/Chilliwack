from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    microsoft_id = db.Column(db.String(50), unique=True, nullable=False)  # Stores Microsoft ID
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    profile_picture = db.Column(db.String(200))  # Optional field

    def __repr__(self):
        return f"<User {self.name}>"
