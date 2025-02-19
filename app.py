from flask import Flask, render_template, url_for, redirect, flash, request, session
import os
from dotenv import load_dotenv
from msal import ConfidentialClientApplication
from flask_session import Session
import requests
from flask_migrate import Migrate
from models import db, User, Role
import urllib.parse
from decorators import role_required, role_not_allowed
from sqlalchemy.orm import joinedload



load_dotenv()

# Get database credentials from .env
DB_SERVER = os.environ.get("DB_SERVER", "your-server.database.windows.net")
DB_NAME = os.environ.get("DB_NAME", "your-database-name")
DB_USERNAME = os.environ.get("DB_USERNAME", "your-db-username")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "your-db-password")

# SQLAlchemy connection string paramaters
params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USERNAME};"
    f"PWD={DB_PASSWORD};"
)

GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

# Configurations + setups
# Flask Application setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

# Configure MySQL database
app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy & Migrate
db.init_app(app)
migrate = Migrate(app, db)  # Enables migrations

# Flask Session setup
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# MSAL configuration
CLIENT_ID = os.environ.get("CLIENT_ID", "your_client_id")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "your_client_secret")
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["User.Read"]  # Adjust scopes based on required permissions

# Initialize MSAL Confidential Client
msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    client_credential=CLIENT_SECRET,
    authority=AUTHORITY)


# Fetches the signed-in user's profile from Microsoft Graph API
def get_user_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{GRAPH_API_BASE_URL}/me", headers=headers)
    return response.json() if response.status_code == 200 else None

# Initializes roles
def create_default_roles():
    roles = ["administrator", "basicuser", "privlageduser", "DEACTIVATED"]
    
    for role_name in roles:
        existing_role = Role.query.filter_by(name=role_name).first()
        if not existing_role:
            new_role = Role(name=role_name)
            db.session.add(new_role)
    db.session.commit()

with app.app_context():
    db.create_all()  # Ensure tables exist
    create_default_roles()  # Create roles

# Home page (should include basic info and a login button)
@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', subtitle='Home Page', text='This is the home page')

# Redirect users to the Microsoft login page
@app.route("/login")
def login():
    auth_url = msal_app.get_authorization_request_url(
        SCOPES,
        redirect_uri="http://localhost:5000/callback"
    )
    return redirect(auth_url)

# Handles response from Microsoft login & stores user info in db
@app.route("/callback")
def callback():
    if request.args.get("code"):
        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"],
            SCOPES,
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
                profile_picture = f"https://graph.microsoft.com/v1.0/me/photo/$value"  # Fetch profile picture

                # Check if user exists, otherwise create
                with app.app_context():  # Ensure database context
                    existing_user = User.query.filter_by(email=email).first()

                    if not existing_user:
                        default_role = Role.query.filter_by(name="basicuser").first()  # Assign 'basicuser' by default
                        new_user = User(
                            microsoft_id=microsoft_id,
                            name=name,
                            email=email,
                            profile_picture=profile_picture,
                            role=default_role
                        )
                        db.session.add(new_user)
                        db.session.commit()

                    session["user"] = {
                        "name": name,
                        "email": email,
                        "profile_picture": profile_picture,
                        "role": existing_user.role.name if existing_user else "basicuser"
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
        user = User.query.filter_by(email=session["user"]["email"]).first()

    return render_template('dashboard.html', user=user)

# Admin Dashboard
@app.route("/admin")
@role_required("administrator")
def admindashboard():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    with app.app_context():
        user = User.query.options(joinedload(User.role)).filter_by(email=session["user"]["email"]).first()
        users = User.query.options(joinedload(User.role)).all()  # Ensure roles are loaded
        roles = Role.query.all()  # Fetch all roles
    return render_template('admindashboard.html', user=user, users = users, roles = roles)

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
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
    else:
        flash("User not found.", "warning")

    return redirect(url_for("admindashboard"))


# Logs the user out by clearing session
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True, host="localhost")