from flask import Flask, render_template, url_for, redirect, flash, request, session
import os
from dotenv import load_dotenv
from msal import ConfidentialClientApplication
from flask_session import Session
import requests

load_dotenv()
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

# Fetches the signed-in user's profile from Microsoft Graph API
def get_user_profile(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{GRAPH_API_BASE_URL}/me", headers=headers)
    return response.json() if response.status_code == 200 else None

# Flask Application setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')

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

# Handles response from Microsoft login
@app.route("/callback")
def callback():
    if request.args.get("code"):
        result = msal_app.acquire_token_by_authorization_code(
            request.args["code"],
            SCOPES,
            redirect_uri="http://localhost:5000/callback"
        )

        # print("MSAL Token Response:", result) # used to debug

        if "access_token" in result:
            session["user"] = result.get("id_token_claims")
            session["access_token"] = result.get("access_token")
            return redirect(url_for("dashboard"))
        else:
            flash("Login failed: " + str(result.get("error_description")), "danger")
            return redirect(url_for("home"))

    return redirect(url_for("home"))

# Shows the user is logged in
@app.route("/dashboard")
def dashboard():
    if not session.get("access_token"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    user_info = get_user_profile(session["access_token"])
    
    if not user_info:
        flash("Failed to fetch user profile.", "danger")
        return redirect(url_for("home"))

    return render_template('dashboard.html', user=user_info)

# Logs the user out by clearing session
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True, host="localhost")