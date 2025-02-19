from flask import Blueprint, session, redirect, url_for, flash, request
from msal import ConfidentialClientApplication
import requests
from config import Config
from models import db, User, Role, Status
from sqlalchemy.orm import joinedload

auth_bp = Blueprint("auth", __name__)

# Initialize MSAL Confidential Client
msal_app = ConfidentialClientApplication(
    Config.CLIENT_ID,
    client_credential=Config.CLIENT_SECRET,
    authority=Config.AUTHORITY
)

# Fetches the signed-in user's profile from Microsoft Graph API
def get_user_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{Config.GRAPH_API_BASE_URL}/me", headers=headers)
    return response.json() if response.status_code == 200 else None

# Redirect users to the Microsoft login page
@auth_bp.route("/login")
def login():
    auth_url = msal_app.get_authorization_request_url(
        Config.SCOPES,
        redirect_uri="http://localhost:5000/callback"
    )
    return redirect(auth_url)

# Handles response from Microsoft login & stores user info in db
@auth_bp.route("/callback")
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
                with db.session.begin():  # Ensure database context
                    existing_user = User.query.options(joinedload(User.role), joinedload(User.status)).filter_by(email=email).first()

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
                        return redirect(url_for("admin.admindashboard"))                    
                    return redirect(url_for("dashboard"))

        flash("Login failed. Please try again.", "danger")
        return redirect(url_for("home"))

    return redirect(url_for("home"))

# Logs the user out by clearing session
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))