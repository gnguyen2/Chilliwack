from flask import Blueprint, request, flash, redirect, url_for, session, render_template
from decorators import role_required
from models import db, User, Role, Status
from sqlalchemy.orm import joinedload

admin_bp = Blueprint("admin", __name__)

# Admin Dashboard
@admin_bp.route("/admin")
@role_required("administrator")
def admindashboard():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    # Get current user with role
    user = User.query.options(joinedload(User.role)).filter_by(email=session["user"]["email"]).first()
    
    # Get all users with roles and order by status
    users = User.query.options(joinedload(User.role)).order_by(User.status_id).all()
    
    # Fetch all roles
    roles = Role.query.all()
    
    # Get distinct status values
    statuses = Status.query.all()

    # Check if bypass is requested
    if request.args.get("bypass") == "true":
        return render_template("admindashboard.html", user=user, users=users, roles=roles, statuses=statuses)
    
    return render_template('admindashboard.html', user=user, users=users, roles=roles, statuses=statuses)

#update users
@admin_bp.route("/admin/update_role", methods=["POST"])
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

    return redirect(url_for("admin.admindashboard"))

#delete a users
@admin_bp.route("/admin/delete_user/<int:user_id>", methods=["POST"])
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
@admin_bp.route("/admin/status_update", methods=["POST"])
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

    return redirect(url_for("admin.admindashboard"))
