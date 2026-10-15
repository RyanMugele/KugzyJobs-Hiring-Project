from app import db


class Admin(db.Model):
    """
    Model representing an Administrator in the platform.
    Inherits common user functionality through the User relationship.
    """

    __tablename__ = "admin"

    adminId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    userId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), unique=True, nullable=False
    )
    roleDesignation = db.Column(
        db.String(100), default="moderator", nullable=True
    )
    dateCreated = db.Column(
        db.TIMESTAMP, default=db.func.current_timestamp(), nullable=False
    )
    lastUpdated = db.Column(
        db.TIMESTAMP,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="admin")

    def __repr__(self) -> str:
        """
        String representation of the Admin object.

        :return: str - String representation showing adminId and role designation
        """
        return f"Admin(adminId={self.adminId}, userId={self.userId}, role={self.roleDesignation})"

    @property
    def user_type(self):
        """
        Property to specify the type of user for authentication purposes.

        :return: str - The user type
        """
        return self.__tablename__

    def get_id(self) -> int:
        """
        Method used by Flask-Login to retrieve admin id for session management.

        :return: int - Admin ID of the admin
        """
        return self.adminId

    def verifyPortfolio(
        self, portfolioId: int, approved: bool, notes: str = None
    ):
        """
        Verifies or rejects a portfolio submission.

        :param portfolioId: int - ID of the portfolio to verify
        :param approved: bool - Whether to approve or reject the portfolio
        :param notes: str - Optional notes explaining the decision
        :return: bool - True if verification was successful, False otherwise
        """
        from .portfolio import Portfolio

        portfolio = Portfolio.query.get(portfolioId)
        if portfolio:
            portfolio.verificationStatus = (
                "approved" if approved else "rejected"
            )
            if notes:
                portfolio.rejectionReason = notes

            # Update editor verification status if this is their first approved portfolio
            if approved and not portfolio.editor.isVerified:
                approved_portfolios = [
                    p
                    for p in portfolio.editor.portfolios
                    if p.verificationStatus == "approved"
                ]
                if (
                    len(approved_portfolios) == 1
                ):  # This is the first approved portfolio
                    portfolio.editor.isVerified = True

            db.session.commit()
            return True
        return False

    def suspendUser(self, userId: int, reason: str = None):
        """
        Suspends a user account.

        :param userId: int - ID of the user to suspend
        :param reason: str - Optional reason for suspension
        :return: bool - True if suspension was successful, False otherwise
        """
        from .user import User

        user = User.query.get(userId)
        if user:
            user.isActive = False
            db.session.commit()
            return True
        return False

    def reactivateUser(self, userId: int):
        """
        Reactivates a suspended user account.

        :param userId: int - ID of the user to reactivate
        :return: bool - True if reactivation was successful, False otherwise
        """
        from .user import User

        user = User.query.get(userId)
        if user:
            user.isActive = True
            db.session.commit()
            return True
        return False

    def resolveReport(
        self, reportId: int, resolution: str, adminNotes: str = None
    ):
        """
        Resolves a user report with appropriate action.

        :param reportId: int - ID of the report to resolve
        :param resolution: str - Resolution status ('resolved' or 'dismissed')
        :param adminNotes: str - Admin notes on the resolution
        :return: bool - True if resolution was successful, False otherwise
        """
        from .report import Report

        report = Report.query.get(reportId)
        if report:
            report.reportStatus = resolution
            report.resolvedBy = self.userId
            report.resolvedDate = db.func.current_timestamp()
            if adminNotes:
                report.adminNotes = adminNotes

            db.session.commit()
            return True
        return False

    def removeInappropriateContent(self, portfolioId: int, reason: str):
        """
        Removes inappropriate portfolio content.

        :param portfolioId: int - ID of the portfolio to remove
        :param reason: str - Reason for content removal
        :return: bool - True if removal was successful, False otherwise
        """
        from .portfolio import Portfolio

        portfolio = Portfolio.query.get(portfolioId)
        if portfolio:
            portfolio.verificationStatus = "rejected"
            portfolio.rejectionReason = f"Content removed: {reason}"
            db.session.commit()
            return True
        return False

    def resetUserPassword(self, userId: int):
        """
        Initiates a password reset for a user.

        :param userId: int - ID of the user whose password to reset
        :return: str|None - Reset token if successful, None otherwise
        """
        from .user import User
        from .password_reset_token import PasswordResetToken
        from utilities.securities import generate_secure_token
        from datetime import datetime
        from datetime import timedelta

        user = User.query.get(userId)
        if user:
            token = generate_secure_token()
            expiry = datetime.utcnow() + timedelta(hours=24)

            reset_token = PasswordResetToken(
                userId=userId, token=token, expiresAt=expiry
            )

            db.session.add(reset_token)
            db.session.commit()
            return token
        return None

    def getPendingPortfolios(self):
        """
        Retrieves all portfolio submissions pending verification.

        :return: list - List of Portfolio objects pending verification
        """
        from .portfolio import Portfolio

        return Portfolio.query.filter_by(verificationStatus="pending").all()

    def getPendingReports(self):
        """
        Retrieves all reports pending resolution.

        :return: list - List of Report objects pending resolution
        """
        from .report import Report

        return Report.query.filter_by(reportStatus="pending").all()

    def getSystemStatistics(self):
        """
        Generates basic system statistics for admin dashboard.

        :return: dict - Dictionary containing various system statistics
        """
        from .job import Job
        from .user import User
        from .editor import Editor
        from .rating import Rating
        from .portfolio import Portfolio

        stats = {
            "total_users": User.query.count(),
            "total_creators": User.query.filter_by(userType="creator").count(),
            "total_editors": User.query.filter_by(userType="editor").count(),
            "verified_editors": db.session.query(User)
            .join(Editor)
            .filter(Editor.isVerified == True)
            .count(),
            "total_jobs": Job.query.count(),
            "completed_jobs": Job.query.filter_by(status="completed").count(),
            "pending_portfolios": Portfolio.query.filter_by(
                verificationStatus="pending"
            ).count(),
            "total_ratings": Rating.query.count(),
            "active_users": User.query.filter_by(isActive=True).count(),
        }

        return stats

    @classmethod
    def getSuperAdmins(cls):
        """
        Retrieves all super administrators.

        :return: list - List of Admin objects with super admin role
        """
        return cls.query.filter_by(roleDesignation="Super Admin").all()

    @classmethod
    def getModerators(cls):
        """
        Retrieves all moderators.

        :return: list - List of Admin objects with moderator role
        """
        return cls.query.filter_by(roleDesignation="moderator").all()
