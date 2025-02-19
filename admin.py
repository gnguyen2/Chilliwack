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
    
    return render_template('admindashboard.html', user=user, sers=users, roles=roles, statuses=statuses)

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

    return redirect(url_for("admindashboard"))