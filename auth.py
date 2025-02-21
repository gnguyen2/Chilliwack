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

            if not user_info:
                flash("Failed to retrieve user info.", "danger")
                return redirect(url_for("home"))

            microsoft_id = user_info.get("id")
            name = user_info.get("displayName")
            email = user_info.get("mail") or user_info.get("userPrincipalName")  # Email might be under different keys

            if not email:
                flash("No email found for this Microsoft account.", "danger")
                return redirect(url_for("home"))

            # Check if user exists, otherwise create
            existing_user = User.query.filter_by(email=email).first()

            if not existing_user:
                default_role = Role.query.filter_by(name="basicuser").first()
                default_status = Status.query.filter_by(name="active").first()
                
                new_user = User(
                    microsoft_id=microsoft_id,
                    name=name,
                    email=email,
                    role=default_role,
                    status=default_status
                )
                db.session.add(new_user)
                db.session.commit()

                user = new_user
            else:
                user = existing_user

            # Store user details in session
            session["user"] = {
                "name": user.name,
                "email": user.email,
                "role": user.role.name,
                "status": user.status.name
            }

            print("User session data:", session["user"])  # Log user info

            # Redirect based on role **(outside if-else to ensure new users are redirected)**
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