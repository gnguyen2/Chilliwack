from functools import wraps
from flask import session, redirect, url_for, flash, request

def role_required(*required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Allow bypass with ?bypass=true
            if request.args.get("bypass") == "true":
                return f(*args, **kwargs)
            
            user_role = session.get("user", {}).get("role")

            if user_role not in required_roles:
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