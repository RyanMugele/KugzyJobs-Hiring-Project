
import getpass

from app import db
from app.models.user import User
from app.models.admin import Admin
from flasky import app


def create_admin():
    email = input("Admin email: ").strip().lower()
    name = input("Admin full name: ").strip()
    password = getpass.getpass("Admin password: ")

    if not email or not name or len(password) < 12:
        print("Provide a name, email, and password of at least 12 characters.")
        return

    with app.app_context():
        existing_user = User.query.filter_by(emailAddress=email).first()

        if existing_user:
            print("An account with this email already exists.")
            return

        user = User(
            fullName=name,
            emailAddress=email,
            userType="admin",
            isActive=True,
        )

        user.password = password

        admin = Admin(
            user=user,
            roleDesignation="Super Admin",
        )

        try:
            db.session.add(user)
            db.session.add(admin)
            db.session.commit()
            print("Administrator account created successfully.")
        except Exception as error:
            db.session.rollback()
            print(f"Administrator creation failed: {error}")


if __name__ == "__main__":
    create_admin()
