from flask import Blueprint, flash, redirect, url_for, session, render_template, send_file
from decorators import role_required
from models import db, User, Role, Status, RCLResponses, TWResponses, Department, ApprovalProcess, GeneralPetition, Delegation, GeneralPetitionDocuments, CAResponses
from sqlalchemy.orm import joinedload
from datetime import datetime


admin_bp = Blueprint("admin", __name__)

# 0 = admin | 1 = TW | 2 = RCL | 3 = Gen‑Pet | 4 = Address Change
DEPT_MODEL_MAP = {
    1: TWResponses,
    2: RCLResponses,
    3: GeneralPetition,
    4: CAResponses
}

# Privlaged user dashboard
@admin_bp.route("/department_dash")
@role_required("administrator", "privilegeduser")
def departmentdashboard():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    # Get current user with role
    user = User.query.options(joinedload(User.role)).filter_by(email=session["user"]["email"]).first()

    forms = []

    # Admin
    if user.department_id == 0:
        forms = (
            TWResponses.query.filter(
                TWResponses.is_finalized == True,
                TWResponses.req_id.isnot(None)
            ).all()
            +
            RCLResponses.query.filter(
                RCLResponses.is_finalized == True,
                RCLResponses.req_id.isnot(None)
            ).all()
            +
            GeneralPetition.query.filter(GeneralPetition.is_finalized == True,
                                         GeneralPetition.is_finalizes == True,
            ).all()
            +
            CAResponses.query.filter(CAResponses.is_finalized == True,
                                         CAResponses.is_finalizes == True,
        )
        )
    # Everyone Else
    else:
        model = DEPT_MODEL_MAP.get(user.department_id)
        if model is None:
            flash("No form type configured for your department.", "warning")
        else:
            if model is not None:
                q = model.query.filter(model.is_finalized.is_(True))

                # Only apply `.request_id.isnot(None)` if the model supports it
                if model in [TWResponses, RCLResponses, CAResponses, GeneralPetition]:
                    q = q.filter(model.request_id.isnot(None))

                forms = q.all()


    # Check if bypass is requested
   
    
    return render_template('departmentdashboard.html', user=user, forms=forms)

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
    ).all()
    submitted_tw_requests = TWResponses.query.filter(
        TWResponses.is_finalized == True,
    ).all()
    submitted_genpet_form = GeneralPetition.query.filter(
        GeneralPetition.is_finalized == True,
    ).all()
    submitted_ca_requests = CAResponses.query.filter(
        CAResponses.is_finalized == True,
    ).all()
    # Combine RCL and TW requests into a single list
    pending_requests = submitted_rcl_requests + submitted_tw_requests + submitted_genpet_form + submitted_ca_requests

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

        # If the user is an admin, set their department to 0 (all departments)
        if new_role_id == "1":
            user.department_id = "0"

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

    current_user_email = session.get("user", {}).get("email")
    if not current_user_email:
        flash("Invalid session. Please log in again.", "danger")
        return redirect(url_for("home"))

    # Prevent self-deletion
    if user.email == current_user_email:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.admindashboard"))

    # Prevent deleting the last administrator
    if user.role.name == "administrator":
        admin_count = User.query.join(Role).filter(Role.name == "administrator").count()
        if admin_count <= 1:
            flash("Cannot delete the last remaining administrator.", "danger")
            return redirect(url_for("admin.admindashboard"))

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

@admin_bp.route("/admin/approve_request/<int:dept_id>/<int:user_id>", methods=["POST"])
@role_required("administrator")
def approve_request(dept_id, user_id):
    # Determine model based on department ID
    model = {
        1: TWResponses,
        2: RCLResponses,
        3: GeneralPetition,
        4: CAResponses
    }.get(dept_id)

    if not model:
        flash("Invalid department selected.", "danger")
        return redirect(url_for("admin.admindashboard"))

    # Look up the user's request in that model
    request_entry = model.query.filter_by(user_id=user_id).order_by(model.id.desc()).first()

    if not request_entry:
        flash(f"No request found for user ID {user_id} in department {dept_id}.", "warning")
        return redirect(url_for("admin.admindashboard"))

    # Finalize and approve the form
    request_entry.is_finalized = True

    # Set department-specific status if needed
    if hasattr(request_entry, "approval_status"):
        request_entry.approval_status = 3  # assuming 3 = approved

    db.session.commit()
    flash(f"{model.__tablename__} form for user {user_id} has been approved.", "success")
    return redirect(url_for("admin.admindashboard"))


@admin_bp.route("/admin/reject_request/<int:dept_id>/<int:user_id>", methods=["POST"])
@role_required("administrator")
def reject_request(dept_id, user_id):
    # Determine model based on department ID
    model = {
        1: TWResponses,
        2: RCLResponses,
        3: GeneralPetition,
        4: CAResponses
    }.get(dept_id)

    if not model:
        flash("Invalid department selected.", "danger")
        return redirect(url_for("admin.admindashboard"))

    # Look up the user's request in that model
    request_entry = model.query.filter_by(user_id=user_id).order_by(model.id.desc()).first()

    if not request_entry:
        flash(f"No request found for user ID {user_id} in department {dept_id}.", "warning")
        return redirect(url_for("admin.admindashboard"))

    # Finalize and approve the form
    request_entry.is_finalized = True

    # Set department-specific status if needed
    if hasattr(request_entry, "approval_status"):
        request_entry.approval_status = 4  # assuming 3 = approved

    db.session.commit()
    flash(f"{model.__tablename__} form for user {user_id} has been rejected.", "success")
    return redirect(url_for("admin.admindashboard"))


@admin_bp.route("/admin/view_request/<int:dept_id>/<int:user_id>")
@role_required("administrator")
def view_request(dept_id, user_id):
    model = {
        1: TWResponses,
        2: RCLResponses,
        3: GeneralPetition,
        4: CAResponses
    }.get(dept_id)

    if not model:
        flash("Invalid department selected.", "danger")
        return redirect(url_for("admin.admindashboard"))
    # Fetch the request, checking both RCL and Withdrawal tables
    request_entry = model.query.filter_by(user_id=user_id).order_by(model.id.desc()).first()


    return render_template("view_request.html", request=request_entry)

@admin_bp.route("/admin/download_pdf/<int:dept_id>/<int:user_id>")
@role_required("administrator")
def download_pdf(request_id):
    request_entry = RCLResponses.query.get(request_id) or TWResponses.query.get(request_id) or GeneralPetition.query.get(request_id) or CAResponses.query.get(request_id)

    if request_entry and request_entry.pdf_path:
        return send_file(request_entry.pdf_path, as_attachment=True)

    flash("PDF not found for this request!", "warning")
    return redirect(url_for("admin.view_request", dept_id=dept_id, user_id=user_id))

# Admin route for departments & roles page
@admin_bp.route("/admin/departments_roles", methods=["GET", "POST"])
@role_required("administrator")
def departments_roles():
    if not session.get("user"):
        flash("Please log in first.", "warning")
        return redirect(url_for("home"))

    user = User.query.filter_by(email=session["user"]["email"]).first()

    departments = Department.query.order_by(Department.name).all()
    roles = Role.query.order_by(Role.name).all()
    users = User.query.order_by(User.name).all()

    return render_template(
        "departments_roles.html",
        departments=departments,
        user=user,
        roles=roles,
        users=users
    )

# Update a user's department and/or role
@admin_bp.route("/admin/update_user_assignment", methods=["POST"])
@role_required("administrator")
def update_user_assignment():
    user_id = request.form.get("user_id")
    dept_id = request.form.get("department_id") or None
    role_id = request.form.get("role_id")

    user = User.query.get(user_id)

    if user:
        if not role_id:
            flash("Role is required when assigning a user.", "danger")
            return redirect(url_for("admin.departments_roles"))

        # Save previous department before updating
        previous_dept = user.department_id

        # Update the user
        user.department_id = dept_id
        user.role_id = role_id
        db.session.commit()
        parent_id = session["user"]["id"]


        # Log the delegation
        new_delegation = Delegation(
            from_parent_id = parent_id,  # assuming Flask-Login is used
            to_child_id=user_id,
            dept_from=previous_dept,
            dept_to=dept_id,
            date=datetime.utcnow()
        )

        db.session.add(new_delegation)
        db.session.commit()

        flash(f"Updated department/role for {user.name} and logged delegation.", "success")
    else:
        flash("User not found.", "danger")

    return redirect(url_for("admin.departments_roles"))

# View pending approvals & history
@admin_bp.route("/admin/approvals", methods=["GET"])
@role_required("administrator")
def approvals():
    form_type = request.args.get("form_type")
    user_id = request.args.get("user_id")
    dept_id = request.args.get("department_id")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Start query
    approvals_query = ApprovalProcess.query

    if form_type:
        try:
            approvals_query = approvals_query.filter(ApprovalProcess.form_type == int(form_type))
        except ValueError:
            flash("Invalid form type filter.", "warning")

    if user_id:
        try:
            approvals_query = approvals_query.filter(ApprovalProcess.user_id == int(user_id))
        except ValueError:
            flash("Invalid user ID filter.", "warning")

    if dept_id:
        try:
            approvals_query = approvals_query.filter(ApprovalProcess.form_type == int(dept_id))
        except ValueError:
            flash("Invalid department ID filter.", "warning")

    if start_date:
        approvals_query = approvals_query.filter(ApprovalProcess.decision_date >= start_date)
    if end_date:
        approvals_query = approvals_query.filter(ApprovalProcess.decision_date <= end_date)

    approvals = approvals_query.order_by(ApprovalProcess.decision_date.desc()).all()

    # Separate pending and historical
    pending_approvals = [a for a in approvals if a.status == "pending"]
    history = [a for a in approvals if a.status != "pending"]

    # Supporting context data
    users = User.query.all()
    departments = Department.query.all()
    current_user = User.query.filter_by(email=session["user"]["email"]).first()

    return render_template(
        "pending_approvals.html",
        pending_approvals=pending_approvals,
        history=history,
        users=users,
        departments=departments,
        user=current_user
    )
