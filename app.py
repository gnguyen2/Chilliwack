from flask import Flask, render_template, url_for, redirect, flash, request, session
from msal import ConfidentialClientApplication
from flask_session import Session
import requests
from flask_migrate import Migrate
from models import db, User, Role, Status
from decorators import role_required, role_not_allowed
from sqlalchemy.orm import joinedload
from config import Config


# Configurations + setups
# Flask Application setup
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy & Migrate
db.init_app(app)
migrate = Migrate(app, db)  # Enables migrations

Session(app)

# Initialize MSAL Confidential Client
msal_app = ConfidentialClientApplication(
    Config.CLIENT_ID,
    client_credential=Config.CLIENT_SECRET,
    authority=Config.AUTHORITY)


# Fetches the signed-in user's profile from Microsoft Graph API
def get_user_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{Config.GRAPH_API_BASE_URL}/me", headers=headers)
    return response.json() if response.status_code == 200 else None

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

# Redirect users to the Microsoft login page
@app.route("/login")
def login():
    auth_url = msal_app.get_authorization_request_url(
        Config.SCOPES,
        redirect_uri="http://localhost:5000/callback"
    )
    return redirect(auth_url)

# Handles response from Microsoft login & stores user info in db
@app.route("/callback")
def callback():
    if request.args.get("code"):
        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"],
            Config.SCOPES,
            redirect_uri="http://localhost:5000/callback"
        )

        if "access_token" in result:
            session["access_token"] = result.get("access_token")

            # Fetch user profile from Microsoft Graph API
            user_info = get_user_profile(session["access_token"])

            if user_info:
                microsoft_id = user_info.get("id")
                name = user_info.get("displayName")
                email = user_info.get("mail") or user_info.get("userPrincipalName")  # Email might be under different keys

                # Check if user exists, otherwise create
                with app.app_context():  # Ensure database context
                    existing_user = User.query.filter_by(email=email).first()

                    if not existing_user:
                        default_role = Role.query.filter_by(name="basicuser").first()  # Assign 'basicuser' by default
                        default_status = Status.query.filter_by(name="active").first()  # Assign 'active' by default
                        new_user = User(
                            microsoft_id=microsoft_id,
                            name=name,
                            email=email,
                            role=default_role,
                            status=default_status
                        )
                        db.session.add(new_user)
                        db.session.commit()

                    session["user"] = {
                        "name": name,
                        "email": email,
                        "role": existing_user.role.name if existing_user else "basicuser",
                        "status": existing_user.status.name if existing_user else "active"

                    }
                    # Redirect based on role
                    if session["user"]["role"] == "administrator":
                        return redirect(url_for("admindashboard"))                    
                    return redirect(url_for("dashboard"))

        flash("Login failed. Please try again.", "danger")
        return redirect(url_for("home"))

    return redirect(url_for("home"))

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

# Admin Dashboard
@app.route("/admin")
@role_required("administrator")
def admindashboard():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    with app.app_context():
        # Get current user with role
        user = User.query.options(joinedload(User.role)).filter_by(email=session["user"]["email"]).first()
        
        # Get all users with roles and order by status
        users = User.query.options(joinedload(User.role)).order_by(User.status_id).all()
        
        # Fetch all roles
        roles = Role.query.all()
        
        # Get distinct status values
        statuses = Status.query.all()
        
        return render_template('admindashboard.html', user=user, sers=users, roles=roles, statuses=statuses)

#update users
@app.route("/admin/update_role", methods=["POST"])
@role_required("administrator")
def update_user_role():
    user_id = request.form.get("user_id")
    new_role_id = request.form.get("role_id")

    user = User.query.get(user_id)
    if user and new_role_id:
        user.role_id = new_role_id
        db.session.commit()
        flash("User role updated successfully!", "success")
    else:
        flash("Failed to update user role.", "warning")

    return redirect(url_for("admindashboard"))


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


# Logs the user out by clearing session
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True, host="localhost")