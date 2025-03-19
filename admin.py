from flask import Blueprint, request, flash, redirect, url_for, session, render_template, send_file
from decorators import role_required
from models import db, User, Role, Status, RCLResponses, TWResponses
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

        # Fetch only submitted (finalized) requests where request_id is not null
    submitted_rcl_requests = RCLResponses.query.filter(
        RCLResponses.is_finalized == True,
        RCLResponses.request_id.isnot(None)
    ).all()
    submitted_tw_requests = TWResponses.query.filter(
        TWResponses.is_finalized == True,
        TWResponses.request_id.isnot(None)
    ).all()

    # Combine RCL and TW requests into a single list
    pending_requests = submitted_rcl_requests + submitted_tw_requests

    # Check if bypass is requested
    if request.args.get("bypass") == "true":
        return render_template('admindashboard.html', user=user, users=users, roles=roles, statuses=statuses, pending_requests=pending_requests)
    
    return render_template('admindashboard.html', user=user, users=users, roles=roles, statuses=statuses, pending_requests=pending_requests)

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
        return redirect(url_for("admin.admindashboard"))

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

    return redirect(url_for("admin.admindashboard"))

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

#handle requests
@admin_bp.route("/admin/approve_request/<int:request_id>", methods=["POST"])
@role_required("administrator")
def approve_request(request_id):
    print("REQUEST: ", request_id)
    # Try finding the request in RCLResponses
    request_entry = RCLResponses.query.get(request_id)
    
    if not request_entry:
        # If not found in RCL, check in TWResponses
        request_entry = TWResponses.query.get(request_id)

    if request_entry:
        request_entry.is_finalized = True  # Mark as finalized
        request_entry.status = "approved"
        db.session.commit()
        
        flash(f"Request {request_id} has been approved.", "success")
    else:
        flash(f"Request {request_id} not found.", "warning")

    return redirect(url_for("admin.admindashboard"))

@admin_bp.route("/admin/reject_request/<int:request_id>", methods=["POST"])
@role_required("administrator")
def reject_request(request_id):
    # Try finding the request in RCLResponses
    request_entry = RCLResponses.query.get(request_id)
    
    if not request_entry:
        # If not found in RCL, check in TWResponses
        request_entry = TWResponses.query.get(request_id)

    if request_entry:
        request_entry.is_finalized = True  # Mark as finalized
        request_entry.status = "rejected"
        db.session.commit()
        
        flash(f"Request {request_id} has been rejected.", "danger")
    else:
        flash(f"Request {request_id} not found.", "warning")

    return redirect(url_for("admin.admindashboard"))

@admin_bp.route("/admin/view_request/<int:request_id>")
@role_required("administrator")
def view_request(request_id):
    # Fetch the request, checking both RCL and Withdrawal tables
    request_entry = RCLResponses.query.get(request_id) or TWResponses.query.get(request_id)

    if not request_entry:
        flash(f"Request {request_id} not found.", "warning")
        return redirect(url_for("admin.admindashboard"))

    return render_template("view_request.html", request=request_entry)

@admin_bp.route("/admin/download_pdf/<int:request_id>")
@role_required("administrator")
def download_pdf(request_id):
    request_entry = RCLResponses.query.get(request_id) or TWResponses.query.get(request_id)

    if request_entry and request_entry.pdf_path:
        return send_file(request_entry.pdf_path, as_attachment=True)

    flash("PDF not found for this request!", "warning")
    return redirect(url_for("admin.view_request", request_id=request_id))