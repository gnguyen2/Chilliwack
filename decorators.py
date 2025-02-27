from functools import wraps
from flask import session, redirect, url_for, flash, request

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Allow bypass if bypass=true is in URL
            if request.args.get("bypass") == "true":
                return f(*args, **kwargs)
            
            if "user" not in session or session["user"].get("role") != required_role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_not_allowed(blocked_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" in session and session["user"].get("role") == blocked_role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("home"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator