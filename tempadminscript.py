from app import db, User, Role, app

def update_user_role(email, new_role_name):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        role = Role.query.filter_by(name=new_role_name).first()

        if user and role:
            user.role = role
            db.session.commit()
            print(f"Updated {user.name}'s role to {new_role_name}")
        else:
            print("User or role not found.")

def update_user_status(email, new_status_name):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        status = Role.query.filter_by(name=new_status_name).first()

        if user and status:
            user.status = status
            db.session.commit()
            print(f"Updated {user.name}'s status to {new_status_name}")
        else:
            print("User or status not found.")

# Makes user administrator:
update_user_role("akkisitu@cougarnet.uh.edu", "administrator")
update_user_status("akkisitu@cougarnet.uh.edu", "active")