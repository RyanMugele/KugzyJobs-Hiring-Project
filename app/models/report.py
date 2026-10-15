from app import db


class Report(db.Model):
    """
    Model representing a Report for inappropriate content or user behavior.
    Supports content moderation and community safety features.
    """

    __tablename__ = "report"

    reportId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    reporterId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), nullable=False
    )
    reportedUserId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), nullable=True
    )
    reportedPortfolioId = db.Column(
        db.Integer, db.ForeignKey("portfolio.portfolioId"), nullable=True
    )
    reportReason = db.Column(db.Text, nullable=False)
    reportStatus = db.Column(
        db.Enum("pending", "reviewed", "resolved"),
        default="pending",
        nullable=False,
    )
    adminNotes = db.Column(db.Text, nullable=True)
    resolvedBy = db.Column(
        db.Integer, db.ForeignKey("user.userId"), nullable=True
    )
    resolvedDate = db.Column(db.TIMESTAMP, nullable=True)
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
    reporter = db.relationship(
        "User", foreign_keys=[reporterId], back_populates="reports"
    )
    reportedUser = db.relationship(
        "User", foreign_keys=[reportedUserId], back_populates="reportedReports"
    )
    reportedPortfolio = db.relationship(
        "Portfolio",
        foreign_keys=[reportedPortfolioId],
        back_populates="reports",
    )
    resolver = db.relationship(
        "User", foreign_keys=[resolvedBy], back_populates="resolvedReports"
    )

    def __repr__(self) -> str:
        """
        String representation of the Report object.

        :return: str - String representation showing report details
        """
        return f"Report(reportId={self.reportId}, status={self.reportStatus}, reporterId={self.reporterId})"

    def updateStatus(
        self, newStatus: str, adminNotes: str = None, resolvedBy: int = None
    ):
        """
        Updates the report status and resolution details.

        :param newStatus: str - New status ('pending', 'reviewed', 'resolved')
        :param adminNotes: str - Admin notes about the resolution
        :param resolvedBy: int - ID of the admin resolving the report
        :return: bool - True if update was successful, False otherwise
        """
        valid_statuses = ["pending", "reviewed", "resolved"]
        if newStatus not in valid_statuses:
            return False

        self.reportStatus = newStatus

        if adminNotes:
            self.adminNotes = adminNotes

        if newStatus == "resolved":
            self.resolvedBy = resolvedBy
            self.resolvedDate = db.func.current_timestamp()

        db.session.commit()
        return True

    def markAsReviewed(self, adminNotes: str = None):
        """
        Marks the report as reviewed by an admin.

        :param adminNotes: str - Optional admin notes
        :return: None
        """
        self.reportStatus = "reviewed"
        if adminNotes:
            self.adminNotes = adminNotes
        db.session.commit()

    def resolveReport(self, resolvedBy: int, adminNotes: str = None):
        """
        Resolves the report with final action taken.

        :param resolvedBy: int - ID of the admin resolving the report
        :param adminNotes: str - Admin notes about the resolution
        :return: None
        """
        self.reportStatus = "resolved"
        self.resolvedBy = resolvedBy
        self.resolvedDate = db.func.current_timestamp()
        if adminNotes:
            self.adminNotes = adminNotes
        db.session.commit()

    def getReportDetails(self):
        """
        Returns comprehensive report details for admin review.

        :return: dict - Dictionary containing report information
        """
        return {
            "report_id": self.reportId,
            "reporter_name": self.reporter.fullName
            if self.reporter
            else "Unknown",
            "reporter_email": self.reporter.emailAddress
            if self.reporter
            else "Unknown",
            "reported_user_name": self.reportedUser.fullName
            if self.reportedUser
            else None,
            "reported_user_email": self.reportedUser.emailAddress
            if self.reportedUser
            else None,
            "reported_portfolio_title": self.reportedPortfolio.title
            if self.reportedPortfolio
            else None,
            "report_reason": self.reportReason,
            "status": self.reportStatus.title(),
            "admin_notes": self.adminNotes,
            "resolver_name": self.resolver.fullName if self.resolver else None,
            "submitted_date": self.dateCreated.strftime("%Y-%m-%d %H:%M"),
            "resolved_date": self.resolvedDate.strftime("%Y-%m-%d %H:%M")
            if self.resolvedDate
            else None,
            "is_user_report": bool(self.reportedUserId),
            "is_portfolio_report": bool(self.reportedPortfolioId),
            "days_pending": (
                db.func.current_timestamp() - self.dateCreated
            ).days
            if self.reportStatus == "pending"
            else 0,
        }

    def getReportType(self):
        """
        Determines the type of report based on what was reported.

        :return: str - Type of report ('user_behavior', 'portfolio_content', 'unknown')
        """
        if self.reportedUserId:
            return "user_behavior"
        elif self.reportedPortfolioId:
            return "portfolio_content"
        else:
            return "unknown"

    def isPending(self):
        """
        Checks if the report is still pending review.

        :return: bool - True if report is pending, False otherwise
        """
        return self.reportStatus == "pending"

    def isResolved(self):
        """
        Checks if the report has been resolved.

        :return: bool - True if report is resolved, False otherwise
        """
        return self.reportStatus == "resolved"

    def getDaysPending(self):
        """
        Calculates how many days the report has been pending.

        :return: int - Number of days since report was submitted
        """
        from datetime import datetime

        if self.reportStatus == "resolved" and self.resolvedDate:
            return (self.resolvedDate - self.dateCreated).days
        else:
            return (datetime.utcnow() - self.dateCreated).days

    @classmethod
    def submitReport(
        cls,
        reporterId: int,
        reportReason: str,
        reportedUserId: int = None,
        reportedPortfolioId: int = None,
    ):
        """
        Submits a new report for inappropriate content or behavior.

        :param reporterId: int - ID of the user submitting the report
        :param reportReason: str - Reason for the report
        :param reportedUserId: int - ID of the reported user (optional)
        :param reportedPortfolioId: int - ID of the reported portfolio (optional)
        :return: Report|None - Created Report object or None if validation fails
        """
        # Validate that at least one target is specified
        if not reportedUserId and not reportedPortfolioId:
            return None

        # Prevent self-reporting
        if reportedUserId == reporterId:
            return None

        # Check for duplicate reports (same reporter, same target, within 24 hours)
        from datetime import datetime
        from datetime import timedelta

        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        existing_report = cls.query.filter(
            cls.reporterId == reporterId,
            cls.dateCreated >= recent_cutoff,
            (
                (cls.reportedUserId == reportedUserId)
                if reportedUserId
                else True
            ),
            (
                (cls.reportedPortfolioId == reportedPortfolioId)
                if reportedPortfolioId
                else True
            ),
        ).first()

        if existing_report:
            return None  # Duplicate report

        report = cls(
            reporterId=reporterId,
            reportedUserId=reportedUserId,
            reportedPortfolioId=reportedPortfolioId,
            reportReason=reportReason,
        )

        db.session.add(report)
        db.session.commit()
        return report

    @classmethod
    def getPendingReports(cls):
        """
        Retrieves all pending reports for admin review.

        :return: list - List of pending Report objects
        """
        return (
            cls.query.filter_by(reportStatus="pending")
            .order_by(cls.dateCreated.asc())
            .all()
        )

    @classmethod
    def getReportsForUser(cls, userId: int):
        """
        Retrieves all reports about a specific user.

        :param userId: int - ID of the reported user
        :return: list - List of Report objects about the user
        """
        return (
            cls.query.filter_by(reportedUserId=userId)
            .order_by(cls.dateCreated.desc())
            .all()
        )

    @classmethod
    def getReportsForPortfolio(cls, portfolioId: int):
        """
        Retrieves all reports about a specific portfolio item.

        :param portfolioId: int - ID of the reported portfolio
        :return: list - List of Report objects about the portfolio
        """
        return (
            cls.query.filter_by(reportedPortfolioId=portfolioId)
            .order_by(cls.dateCreated.desc())
            .all()
        )

    @classmethod
    def getReportsByReporter(cls, reporterId: int):
        """
        Retrieves all reports submitted by a specific user.

        :param reporterId: int - ID of the reporting user
        :return: list - List of Report objects submitted by the user
        """
        return (
            cls.query.filter_by(reporterId=reporterId)
            .order_by(cls.dateCreated.desc())
            .all()
        )

    @classmethod
    def getResolvedReports(cls, resolvedBy: int = None):
        """
        Retrieves resolved reports, optionally filtered by resolver.

        :param resolvedBy: int - Optional ID of the admin who resolved reports
        :return: list - List of resolved Report objects
        """
        query = cls.query.filter_by(reportStatus="resolved")
        if resolvedBy:
            query = query.filter_by(resolvedBy=resolvedBy)
        return query.order_by(cls.resolvedDate.desc()).all()

    @classmethod
    def getReportStatistics(cls):
        """
        Generates comprehensive report statistics for admin dashboard.

        :return: dict - Dictionary containing report statistics
        """
        total_reports = cls.query.count()
        pending_reports = cls.query.filter_by(reportStatus="pending").count()
        reviewed_reports = cls.query.filter_by(reportStatus="reviewed").count()
        resolved_reports = cls.query.filter_by(reportStatus="resolved").count()

        user_reports = cls.query.filter(cls.reportedUserId.isnot(None)).count()
        portfolio_reports = cls.query.filter(
            cls.reportedPortfolioId.isnot(None)
        ).count()

        # Average resolution time for resolved reports
        from sqlalchemy import func

        avg_resolution_time = (
            db.session.query(
                func.avg(
                    func.julianday(cls.resolvedDate)
                    - func.julianday(cls.dateCreated)
                )
            )
            .filter_by(reportStatus="resolved")
            .scalar()
        )

        avg_resolution_days = (
            round(float(avg_resolution_time), 2) if avg_resolution_time else 0
        )

        return {
            "total_reports": total_reports,
            "pending_reports": pending_reports,
            "reviewed_reports": reviewed_reports,
            "resolved_reports": resolved_reports,
            "user_reports": user_reports,
            "portfolio_reports": portfolio_reports,
            "resolution_rate": round(
                (resolved_reports / total_reports * 100)
                if total_reports > 0
                else 0,
                2,
            ),
            "average_resolution_days": avg_resolution_days,
        }

    @classmethod
    def getOverdueReports(cls, daysPending: int = 7):
        """
        Retrieves reports that have been pending for too long.

        :param daysPending: int - Number of days after which a report is considered overdue
        :return: list - List of overdue Report objects
        """
        from datetime import datetime
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=daysPending)
        return (
            cls.query.filter(
                cls.reportStatus == "pending", cls.dateCreated <= cutoff_date
            )
            .order_by(cls.dateCreated.asc())
            .all()
        )
