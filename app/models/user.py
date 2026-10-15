from app import db
from utilities.users import BaseUser


class User(BaseUser):
    """
    Model representing a User in the content creator platform.
    This is the base user model that handles common user functionality.
    """

    __tablename__ = "user"

    userId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    userType = db.Column(db.Enum("creator", "editor", "admin"), nullable=False)
    profilePicture = db.Column(db.String(500), nullable=True)
    averageRating = db.Column(db.Numeric(3, 2), default=0.00, nullable=False)
    totalRatings = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    creator = db.relationship(
        "Creator",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    editor = db.relationship(
        "Editor",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    admin = db.relationship(
        "Admin",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sentMessages = db.relationship(
        "Message",
        foreign_keys="Message.senderId",
        back_populates="sender",
        cascade="all, delete-orphan",
    )
    receivedMessages = db.relationship(
        "Message",
        foreign_keys="Message.receiverId",
        back_populates="receiver",
        cascade="all, delete-orphan",
    )
    givenRatings = db.relationship(
        "Rating",
        foreign_keys="Rating.raterId",
        back_populates="rater",
        cascade="all, delete-orphan",
    )
    receivedRatings = db.relationship(
        "Rating",
        foreign_keys="Rating.rateeId",
        back_populates="ratee",
        cascade="all, delete-orphan",
    )
    reports = db.relationship(
        "Report",
        foreign_keys="Report.reporterId",
        back_populates="reporter",
        cascade="all, delete-orphan",
    )
    reportedReports = db.relationship(
        "Report",
        foreign_keys="Report.reportedUserId",
        back_populates="reportedUser",
        cascade="all, delete-orphan",
    )
    resolvedReports = db.relationship(
        "Report",
        foreign_keys="Report.resolvedBy",
        back_populates="resolver",
        cascade="all, delete-orphan",
    )
    passwordResetTokens = db.relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """
        String representation of the User object.

        :return: str - String representation showing userId and fullName
        """
        return f"User(userId={self.userId}, fullName={self.fullName}, userType={self.userType})"

    @property
    def user_type(self):
        """
        Property to specify the type of user for authentication purposes.

        :return: str - The user type
        """
        return self.__tablename__

    def get_id(self) -> int:
        """
        Method used by Flask-Login to retrieve user id for session management.

        :return: int - User ID of the user
        """
        return self.userId

    def updateAverageRating(self):
        """
        Recalculates and updates the user's average rating based on all received ratings.
        This method should be called whenever a new rating is added.

        :return: None
        """
        if self.totalRatings > 0:
            total_score = sum(
                rating.ratingValue for rating in self.receivedRatings
            )
            self.averageRating = round(total_score / self.totalRatings, 2)
        else:
            self.averageRating = 0.00

        db.session.commit()

    def uploadProfilePicture(self, filePath: str):
        """
        Updates the user's profile picture path.

        :param filePath: str - Path to the uploaded profile picture
        :return: None
        """
        self.profilePicture = filePath
        db.session.commit()

    def getSpecificUserData(self):
        """
        Retrieves user-type specific data based on userType.

        :return: Creator|Editor|Admin|None - The specific user type object
        """
        if self.userType == "creator":
            return self.creator
        elif self.userType == "editor":
            return self.editor
        elif self.userType == "admin":
            return self.admin
        return None

    @classmethod
    def getUsersByType(cls, userType: str):
        """
        Retrieves all users of a specific type.

        :param userType: str - The type of users to retrieve ('creator', 'editor', 'admin')
        :return: list - List of User objects of the specified type
        """
        return cls.query.filter_by(userType=userType).all()

    @classmethod
    def getActiveUsers(cls):
        """
        Retrieves all active users in the platform.

        :return: list - List of active User objects
        """
        return cls.query.filter_by(isActive=True).all()
