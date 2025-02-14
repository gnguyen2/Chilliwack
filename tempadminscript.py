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

# Makes user administrator:
update_user_role("akkisitu@cougarnet.uh.edu", "administrator")
