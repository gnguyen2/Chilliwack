from flask import Flask, render_template, url_for, redirect, flash, request, session
from flask_session import Session
from flask_migrate import Migrate
from models import db, User, Role, Status
from decorators import role_required, role_not_allowed
from sqlalchemy.orm import joinedload

from config import Config
from auth import auth_bp
from admin import admin_bp


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


#delete a users
@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@role_required("administrator")
def delete_user(user_id):
    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("admindashboard"))

    # Check if the logged-in admin is deleting their own account
    if session.get("user") and session["user"].get("email") == user.email:
        db.session.delete(user)
        db.session.commit()
        session.clear()  # Clear session to log out the user
        flash("Your account has been deleted. You have been logged out.", "info")
        return redirect(url_for("home"))  # Redirect to login page

    # Otherwise, just delete the user normally
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully!", "success")

    return redirect(url_for("admindashboard"))

#updates a users status
@app.route("/admin/status_update", methods=["POST"])
@role_required("administrator")
def change_status():
    user_id = request.form.get("user_id")
    new_status_id = request.form.get("status_id")

    user = User.query.get(user_id)
    if user and new_status_id:
        user.status_id = new_status_id
        db.session.commit()
        flash("User status updated successfully!", "success")
    else:
        flash("Failed to update user status.", "warning")

    return redirect(url_for("admindashboard"))




if __name__ == '__main__':
    app.run(debug=True, host="localhost")