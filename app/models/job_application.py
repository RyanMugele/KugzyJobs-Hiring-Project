from app import db


class JobApplication(db.Model):
    """
    Model representing a Job Application submitted by editors.
    Handles the many-to-many relationship between jobs and editors.
    """

    __tablename__ = "job_application"

    jobApplicationId = db.Column(
        db.Integer, autoincrement=True, primary_key=True
    )
    jobId = db.Column(db.Integer, db.ForeignKey("job.jobId"), nullable=False)
    editorId = db.Column(
        db.Integer, db.ForeignKey("editor.editorId"), nullable=False
    )
    proposedRate = db.Column(db.Numeric(10, 2), nullable=False)
    proposedTimeline = db.Column(db.String(100), nullable=True)
    customProposal = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("pending", "accepted", "declined"),
        default="pending",
        nullable=False,
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
    job = db.relationship("Job", back_populates="applications")
    editor = db.relationship("Editor", back_populates="jobApplications")

    # Unique constraint to prevent duplicate applications
    __table_args__ = (
        db.UniqueConstraint(
            "jobId", "editorId", name="unique_job_editor_application"
        ),
    )

    def __repr__(self) -> str:
        """
        String representation of the JobApplication object.

        :return: str - String representation showing application ID and status
        """
        return f"JobApplication(jobApplicationId={self.jobApplicationId}, jobId={self.jobId}, editorId={self.editorId}, status={self.status})"

    def updateProposal(
        self,
        proposedRate: float = None,
        proposedTimeline: str = None,
        customProposal: str = None,
    ):
        """
        Updates the application proposal details (only allowed when status is 'pending').

        :param proposedRate: float - New proposed rate
        :param proposedTimeline: str - New proposed timeline
        :param customProposal: str - New custom proposal text
        :return: bool - True if update was successful, False if application is no longer editable
        """
        if self.status != "pending":
            return False

        if proposedRate is not None:
            self.proposedRate = proposedRate
        if proposedTimeline is not None:
            self.proposedTimeline = proposedTimeline
        if customProposal is not None:
            self.customProposal = customProposal

        db.session.commit()
        return True

    def withdrawApplication(self):
        """
        Withdraws the application (only allowed when status is 'pending').

        :return: bool - True if withdrawal was successful, False otherwise
        """
        if self.status == "pending":
            db.session.delete(self)
            db.session.commit()
            return True
        return False

    def acceptApplication(self):
        """
        Marks this application as accepted and declines all other applications for the same job.
        Also updates the job status and selects the editor.

        :return: bool - True if acceptance was successful, False otherwise
        """
        if self.status == "pending" and self.job.status == "posted":
            # Update this application
            self.status = "accepted"

            # Update the job
            self.job.selectedEditorId = self.editorId
            self.job.status = "in_progress"

            # Decline all other pending applications for this job
            for application in self.job.applications:
                if (
                    application.jobApplicationId != self.jobApplicationId
                    and application.status == "pending"
                ):
                    application.status = "declined"

            db.session.commit()
            return True
        return False

    def declineApplication(self):
        """
        Marks this application as declined.

        :return: bool - True if decline was successful, False otherwise
        """
        if self.status == "pending":
            self.status = "declined"
            db.session.commit()
            return True
        return False

    def isEditable(self):
        """
        Checks if this application can still be edited by the editor.

        :return: bool - True if application is still pending and editable
        """
        return self.status == "pending"

    def getProposalSummary(self):
        """
        Returns a formatted summary of the proposal.

        :return: dict - Dictionary containing proposal summary
        """
        return {
            "rate": f"${self.proposedRate}",
            "timeline": self.proposedTimeline or "Not specified",
            "proposal_length": len(self.customProposal)
            if self.customProposal
            else 0,
            "status": self.status.title(),
            "submitted_date": self.dateCreated.strftime("%Y-%m-%d %H:%M"),
        }

    def compareWithJobBudget(self):
        """
        Compares the proposed rate with the job's budget range.

        :return: str - Comparison result ('within_budget', 'below_budget', 'above_budget', 'no_budget_specified')
        """
        if not self.job.budgetMin and not self.job.budgetMax:
            return "no_budget_specified"

        if self.job.budgetMin and self.proposedRate < self.job.budgetMin:
            return "below_budget"

        if self.job.budgetMax and self.proposedRate > self.job.budgetMax:
            return "above_budget"

        return "within_budget"

    @classmethod
    def getPendingApplications(cls):
        """
        Retrieves all pending job applications across the platform.

        :return: list - List of pending JobApplication objects
        """
        return cls.query.filter_by(status="pending").all()

    @classmethod
    def getAcceptedApplications(cls):
        """
        Retrieves all accepted job applications across the platform.

        :return: list - List of accepted JobApplication objects
        """
        return cls.query.filter_by(status="accepted").all()

    @classmethod
    def getApplicationsByEditor(cls, editorId: int):
        """
        Retrieves all applications submitted by a specific editor.

        :param editorId: int - ID of the editor
        :return: list - List of JobApplication objects by the editor
        """
        return cls.query.filter_by(editorId=editorId).all()

    @classmethod
    def getApplicationsByJob(cls, jobId: int):
        """
        Retrieves all applications for a specific job.

        :param jobId: int - ID of the job
        :return: list - List of JobApplication objects for the job
        """
        return cls.query.filter_by(jobId=jobId).all()

    @classmethod
    def getApplicationsInBudgetRange(cls, minRate: float, maxRate: float):
        """
        Retrieves applications with proposed rates within a specific range.

        :param minRate: float - Minimum proposed rate
        :param maxRate: float - Maximum proposed rate
        :return: list - List of JobApplication objects within rate range
        """
        return cls.query.filter(
            cls.proposedRate >= minRate, cls.proposedRate <= maxRate
        ).all()

    @classmethod
    def getRecentApplications(cls, limit: int = 10):
        """
        Retrieves the most recently submitted applications.

        :param limit: int - Maximum number of applications to return
        :return: list - List of recent JobApplication objects
        """
        return cls.query.order_by(cls.dateCreated.desc()).limit(limit).all()

    @classmethod
    def checkExistingApplication(cls, jobId: int, editorId: int):
        """
        Checks if an editor has already applied for a specific job.

        :param jobId: int - ID of the job
        :param editorId: int - ID of the editor
        :return: JobApplication|None - Existing application or None
        """
        return cls.query.filter_by(jobId=jobId, editorId=editorId).first()
