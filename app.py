from flask import Flask, render_template, url_for, redirect, flash, request, session
from flask_session import Session
from flask_migrate import Migrate
from models import db, User, Role, Status
from decorators import role_not_allowed
from sqlalchemy.orm import joinedload

from config import Config
from auth import auth_bp
from admin import admin_bp
import os
from werkzeug.utils import secure_filename
from datetime import datetime


# Configurations + setups
# Flask Application setup
app = Flask(__name__)
app.config.from_object(Config)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# Initialize SQLAlchemy & Migrate
db.init_app(app)
migrate = Migrate(app, db)  # Enables migrations

Session(app)

# Initializes roles
def create_default_roles():
    roles = ["administrator", "basicuser", "privlageduser"]
    
    for role_name in roles:
        existing_role = Role.query.filter_by(name=role_name).first()
        if not existing_role:
            new_role = Role(name=role_name)
            db.session.add(new_role)
    db.session.commit()

def create_default_statuses():
    statuses = ["active", "deactivated"]
    
    for status_name in statuses:
        existing_status = Status.query.filter_by(name=status_name).first()
        if not existing_status:
            new_status = Status(name=status_name)
            db.session.add(new_status)
    db.session.commit()

with app.app_context():
    db.create_all()  # Ensure tables exist
    create_default_roles()  # Create roles
    create_default_statuses() # Create statuses

@app.before_request
def refresh_user_session():
    if "user" in session:
        user = User.query.filter_by(email=session["user"]["email"]).first()
        if user:
            session["user"]["role"] = user.role.name
    

# Home page (should include basic info and a login button)
@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', subtitle='Home Page', text='This is the home page')

# Shows the user is logged in
@app.route("/dashboard")
@role_not_allowed("DEACTIVATED")
def dashboard():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    with app.app_context():
        # Ensure to eagerly load the 'role' attribute
        user = User.query.options(joinedload(User.role), joinedload(User.status)).filter_by(email=session["user"]["email"]).first()

    return render_template('dashboard.html', user=user)

# upload signature page
@app.route("/upload_signature_page")
def upload_signature_page():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))
    
    return render_template("upload_signature.html")



@app.route("/upload_signature", methods=["POST"])
def upload_signature():
    file = request.files["signature"]

    user = User.query.filter_by(email=session["user"]["email"]).first()
    if "signature" not in request.files or request.files["signature"].filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("upload_signature_page"))

    user_id = user.id  # Get the user's ID
    user_initial = user.name[0].upper()  # Get the first initial of the user's name and capitalize it
    current_date = datetime.now().strftime("%m%d%Y%H%M%S")  # Get the current date in mmddyyyyhhmmss format     

    # Extract the file extension safely
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ""
    if not file_extension:
        flash("File must have an extension!", "danger")
        return redirect(url_for("upload_signature_page"))

    # Construct the custom filename
    user_id = user.id  # Get the user's ID
    user_initial = user.name[0].upper()  # Get the first initial of the user's name and capitalize it
    current_date = datetime.now().strftime("%m%d%Y%H%M%S")  # Get the current date in mmddyyyyhhmmss format
    filename = f"{user_id}_{user_initial}_{current_date}.{file_extension}"
    filename = secure_filename(filename)  # Sanitize the custom filename


    # Ensure the directory exists
    signature_folder = "static/signatures"
    if not os.path.exists(signature_folder):
        os.makedirs(signature_folder)

    file_path = os.path.join(signature_folder, filename)
    file.save(file_path)

    # Update the user record
    #user = User.query.filter_by(email=session["user"]["email"]).first() MOVED TO TOP OF DEF
    user.signature_path = f"signatures/{filename}"
    user.updated_at = datetime.utcnow()  # Force timestamp update
    db.session.commit()

    # Refresh session data
    session["user"]["signature_path"] = user.signature_path  # Ensure session reflects new path
    session.modified = True

    flash("Signature uploaded successfully!", "success")
    return redirect(url_for("dashboard"))

# upload signature page
@app.route("/upload_rcl_page")
def upload_rcl_page():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))
    
    return render_template("upload_rcl.html")

@app.route("/upload_rcl", methods=['POST'])
def upload_rcl():
     #queries the user info from records table
    user = User.query.filter_by(email=session["user"]["email"]).first()
    
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    if "rcl" not in request.files or request.files["rcl"].filename == "":
        flash("No file selected!", "danger")
        return redirect(url_for("upload_rcl_page"))
    
    file = request.files["rcl"]
    filename = secure_filename(file.filename)

    # Ensure the directory exists
    signature_folder = "static/rcl_forms"
    if not os.path.exists(signature_folder):
        os.makedirs(signature_folder)

    
    file_path = os.path.join(signature_folder, filename)
    file.save(file_path)

    # Update the user record
     #user = User.query.filter_by(email=session["user"]["email"]).first() MOVED TO TOP OF DEF 
    user.rcl_path = f"rcl_forms/{filename}"
    user.updated_at = datetime.utcnow()  # Force timestamp update
    db.session.commit()

    # Refresh session data
    session["user"]["rcl_path"] = user.rcl_path  # Ensure session reflects new path
    session.modified = True

    flash("Signature uploaded successfully!", "success")
    return redirect(url_for("dashboard"))

if __name__ == '__main__':
    app.run(debug=True, host="localhost")