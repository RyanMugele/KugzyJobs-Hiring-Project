import os
from datetime import datetime

import flask_login
from flask import url_for
from flask import session
from flask import current_app
from sqlalchemy import inspect
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer

from app import db

from utilities.file_saver import save_image
from utilities.file_saver import delete_file
from utilities.email_utils import send_email
from utilities.securities import get_gravatar_hash


class BaseUser(flask_login.UserMixin, db.Model):
    """
    Base class for user models.
    """

    __abstract__ = True

    fullName = db.Column(db.String(255), nullable=False)
    emailAddress = db.Column(db.String(255), unique=True, nullable=False)
    passwordHash = db.Column(db.String(255), nullable=False)
    avatarHash = db.Column(db.String(255))
    imageUrl = db.Column(db.String(255))
    lastSeen = db.Column(db.DateTime)
    isActive = db.Column(db.Boolean, default=True)
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)
    lastUpdated = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __init__(self, **kwargs):
        super(BaseUser, self).__init__(**kwargs)

        # Initialize their last seen as the created date
        self.lastSeen = datetime.utcnow()

        # Generate the avatar hash
        if self.emailAddress is not None and self.avatarHash is None:
            self.avatarHash = get_gravatar_hash(self.emailAddress)

    @property
    def user_type(self):
        """
        Must be defined in subclasses to specify the type of user.
        """
        raise NotImplementedError(
            "Subclasses must implement 'user_type' method."
        )

    @classmethod
    def registerAccount(cls, details: dict, isActive=True) -> "BaseUser":
        """
        Create a new user.

        :param details: dict - Details of the user to be created.
        :return: BaseUser - The newly created user instance.
        """
        if not isActive:
            details["isActive"] = False

        user = cls(**details)
        db.session.add(user)
        db.session.commit()
        return user

    def update(self, details: dict) -> "BaseUser":
        """
        Update user details.

        :param details: dict - A dictionary of details to update.
        :return: BaseUser - The updated user instance.
        """
        for key, value in details.items():
            setattr(self, key, value)

        db.session.commit()
        return self

    def has_back_references(self) -> bool:
        """
        Dynamically checks if there are any back-references (related records)
            for this instance.

        :return: True if related records exist, False otherwise.
        """
        # Use SQLAlchemy's inspection tools to find relationships
        mapper = inspect(self.__class__)
        for relationship in mapper.relationships:
            # Query the related table to check for records
            related_class = relationship.mapper.class_
            back_ref_count = (
                db.session.query(related_class)
                .filter(
                    list(relationship.remote_side)[0]
                    == getattr(self, list(relationship.local_columns)[0].key)
                )
                .count()
            )
            if back_ref_count > 0:
                return True
        return False

    def delete(self) -> None:
        """
        Delete the object if there are no back-references.

        :return: None if deletion is successful, raises ValueError otherwise.
        """
        if self.has_back_references():
            raise ValueError(
                f"Deletion denied: {self.__class__.__name__} has related "
                + "records in the database."
            )

        # Proceed with deletion if no back-references exist
        db.session.delete(self)
        db.session.commit()

    def get_id(self) -> int:
        """
        Inherited BaseUserMixin class method used to retrieve user id for
        flask_login

        :return: int - BaseUser ID of the user.
        """
        raise NotImplementedError("Subclasses must implement 'get_id' method.")

    def login(self, details=dict()) -> tuple:
        """
        Logs in the user and marks them as online.

        :param details: dict - Contains password and remember_me boolean
        variable

        :return: tuple - Contains the return status and return message.
        """

        if self.verifyPassword(details.get("password", "")):
            flask_login.login_user(self, details.get("remember_me", False))

            # Mark them as online
            self.lastSeen = None
            db.session.commit()

            # Set user type session variable
            session.permanent = True
            session["user_type"] = self.user_type

            return (1, "Login Successful")

        return (0, "Invalid password")

    def _peaceOut(self) -> None:
        """
        Updates user's last seen timestamp.
        """
        self.lastSeen = datetime.utcnow()
        db.session.commit()

    def logout(self) -> tuple:
        """
        Logs out the user and updates their last seen timestamp.

        :return: tuple - Contains return status and return message.
        """
        # Logout user
        flask_login.logout_user()

        # Update their last seen
        self._peaceOut()

        return (1, "Logout successful")

    @property
    def password(self) -> AttributeError:
        """
        Raise an AttributeError since the password is private only
        """
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password) -> None:
        """
        Hash the user's password
        """
        self.passwordHash = generate_password_hash(password)

    def generateConfirmationToken(self) -> str:
        """
        Generate a confirmation token.

        This method generates a token for confirming the user's email address.

        :return: str - The confirmation token.
        """
        serializer = Serializer(current_app.config["SECRET_KEY"])
        return serializer.dumps(self.emailAddress)

    def sendPasswordResetEmail(self) -> None:
        """
        Send a password reset email to the user.
        """
        token = self.generateConfirmationToken()
        reset_link = url_for(
            f"authentication.{self.user_type}_password_reset",
            token=token,
            _scheme="https",
            _external=True,
        )

        subject = "Password Reset Request"
        send_email(
            [self.emailAddress],
            subject,
            "email/password_reset_request",
            user_name=self.fullName,
            reset_link=reset_link,
        )

    @classmethod
    def confirmPasswordResetToken(cls, token, expiration=3600 * 24):
        """
        Validate password request link provided.
        """
        serializer = Serializer(current_app.config["SECRET_KEY"])

        try:
            data = serializer.loads(token, max_age=expiration)
            user = cls.query.filter_by(emailAddress=data).first()

            return user

        except Exception:
            return None

    @classmethod
    def resetPassword(cls, token, new_password, expiration=3600):
        """
        Reset user's password.

        :param token: str - the token for password reset.
        :param new_password: str - the new password.
        """
        serializer = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = serializer.loads(token, expiration)

        except Exception:
            return False

        user = cls.query.filter_by(emailAddress=data).first()
        if user is None:
            return False

        user.password = new_password
        db.session.commit()

        return True

    def deleteProfileImage(self) -> None:
        """
        Deletes user's profile image.
        """
        # Delete actual file from the file system
        file_path = os.path.join(
            current_app.config["USERS_PROFILE_UPLOAD_PATH"], self.imageURL
        )
        os.remove(file_path)

        # Update the same on the database
        self.imageURL = None
        db.session.commit()

    def updateProfileImage(self, image) -> "BaseUser":
        """
        Update user's profile image.

        :param image: FileStorage - the image file to be uploaded.

        :return self: BaseUser - the updated BaseUser instance.
        """
        # Delete the old image if it exists
        if self.imageURL:
            delete_file(
                os.path.join(
                    current_app.config["USERS_PROFILE_UPLOAD_PATH"],
                    self.imageURL,
                )
            )

        # Save image on file system
        saved_filename = save_image(
            image, current_app.config["USERS_PROFILE_UPLOAD_PATH"]
        )

        # Save filename in database
        self.imageURL = saved_filename
        db.session.add(self)
        db.session.commit()

        return self

    def activateAccount(self) -> None:
        """
        Activate the user's account.
        """
        if self.isActive:
            return

        self.isActive = True
        db.session.commit()

        # Notify user on account activation via email
        subject = "Account Activation"
        send_email(
            [self.emailAddress],
            subject,
            "email/account_activation",
            user=self,
        )

    def deactivateAccount(self) -> None:
        """
        Deactivate the user's account.
        """
        if not self.isActive:
            return

        self.isActive = False
        db.session.commit()

        # Notify user on account deactivation via email
        subject = "Account Deactivation"
        send_email(
            [self.emailAddress],
            subject,
            "email/account_deactivation",
            user=self,
        )

    def verifyPassword(self, password: str) -> bool:
        """
        Verify the provided password with the stored hash.

        :param password: str - The password to verify.
        :return: bool - True if the password matches, False otherwise.
        """
        return check_password_hash(self.passwordHash, password)

    def updatePassword(self, current_password, new_password):
        """
        Updates user's password.

        :param current_password: str - BaseUser's current password.
        :param new_password: str - BaseUser's new password.

        :return self: BaseUser - the updated BaseUser instance.
        """
        if self.verifyPassword(current_password):
            self.password = new_password
            db.session.commit()
            return self

        return

    def getGravatar(self, size=100, default="identicon", rating="g"):
        """
        Generates a Gravatar URL for the user based on their email address.

        :param size: int - The size of the Gravatar image.
        :param default: str - The default image to be displayed if no
        Gravatar is found.
        :param rating: str - The content rating for the image.

        :return: str - The Gravatar URL.
        """
        url = "https://secure.gravatar.com/avatar"

        # Generate avatar hash if it does not exist
        if not self.avatarHash:
            self.avatarHash = get_gravatar_hash(self.emailAddress)
            db.session.commit()

        # Retrieve it for usage
        hash = self.avatarHash
        return "{url}/{hash}?s={size}&d={default}&r={rating}".format(
            url=url, hash=hash, size=size, default=default, rating=rating
        )
