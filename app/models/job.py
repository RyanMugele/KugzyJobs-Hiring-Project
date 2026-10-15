from app import db


class Job(db.Model):
    """
    Model representing a Job posting created by content creators.
    Manages the entire job lifecycle from posting to completion.
    """

    __tablename__ = "job"

    jobId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    creatorId = db.Column(
        db.Integer, db.ForeignKey("creator.creatorId"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budgetMin = db.Column(db.Numeric(10, 2), nullable=True)
    budgetMax = db.Column(db.Numeric(10, 2), nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    requiredSkills = db.Column(db.Text, nullable=True)

    # NLP extracted information
    extractedSkills = db.Column(db.Text, nullable=True)
    extractedStyles = db.Column(db.Text, nullable=True)
    extractedNiches = db.Column(db.Text, nullable=True)

    status = db.Column(
        db.Enum("posted", "in_progress", "completed"),
        default="posted",
        nullable=False,
    )
    selectedEditorId = db.Column(
        db.Integer, db.ForeignKey("editor.editorId"), nullable=True
    )
    completedDate = db.Column(db.TIMESTAMP, nullable=True)
    deliverableUrl = db.Column(db.String(500), nullable=True)
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
    creator = db.relationship("Creator", back_populates="jobs")
    selectedEditor = db.relationship(
        "Editor", foreign_keys=[selectedEditorId], back_populates="selectedJobs"
    )
    applications = db.relationship(
        "JobApplication", back_populates="job", cascade="all, delete-orphan"
    )
    payment = db.relationship(
        "Payment",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )
    ratings = db.relationship(
        "Rating", back_populates="job", cascade="all, delete-orphan"
    )
    messages = db.relationship(
        "Message", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        String representation of the Job object.

        :return: str - String representation showing jobId, title and status
        """
        return (
            f"Job(jobId={self.jobId}, title={self.title}, status={self.status})"
        )

    def updateJobDetails(
        self,
        title: str = None,
        description: str = None,
        budgetMin: float = None,
        budgetMax: float = None,
        deadline=None,
        requiredSkills: str = None,
    ):
        """
        Updates job posting details (only allowed when status is 'posted').

        :param title: str - New job title
        :param description: str - New job description
        :param budgetMin: float - New minimum budget
        :param budgetMax: float - New maximum budget
        :param deadline: date - New deadline
        :param requiredSkills: str - New required skills
        :return: bool - True if update was successful, False if job is no longer editable
        """
        if self.status != "posted":
            return False

        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if budgetMin is not None:
            self.budgetMin = budgetMin
        if budgetMax is not None:
            self.budgetMax = budgetMax
        if deadline is not None:
            self.deadline = deadline
        if requiredSkills is not None:
            self.requiredSkills = requiredSkills

        db.session.commit()
        return True

    def selectEditor(self, editorId: int):
        """
        Selects an editor for this job and updates status to in_progress.

        :param editorId: int - ID of the editor to select
        :return: bool - True if selection was successful, False otherwise
        """
        if self.status == "posted":
            self.selectedEditorId = editorId
            self.status = "in_progress"

            # Update all applications for this job
            for application in self.applications:
                if application.editorId == editorId:
                    application.status = "accepted"
                elif application.status == "pending":
                    application.status = "declined"

            db.session.commit()
            return True
        return False

    def markCompleted(self, deliverableUrl: str = None):
        """
        Marks the job as completed and optionally sets deliverable URL.

        :param deliverableUrl: str - URL to the completed deliverable
        :return: bool - True if job was marked completed, False otherwise
        """
        if self.status == "in_progress":
            self.status = "completed"
            self.completedDate = db.func.current_timestamp()
            if deliverableUrl:
                self.deliverableUrl = deliverableUrl

            db.session.commit()
            return True
        return False

    def uploadDeliverable(self, deliverableUrl: str):
        """
        Uploads the final deliverable for this job.

        :param deliverableUrl: str - URL to the deliverable file
        :return: None
        """
        self.deliverableUrl = deliverableUrl
        db.session.commit()

    def getPendingApplications(self):
        """
        Retrieves all pending applications for this job.

        :return: list - List of pending JobApplication objects
        """
        return [app for app in self.applications if app.status == "pending"]

    def getAcceptedApplication(self):
        """
        Retrieves the accepted application for this job.

        :return: JobApplication|None - The accepted application or None
        """
        return next(
            (app for app in self.applications if app.status == "accepted"), None
        )

    def getBudgetRange(self):
        """
        Returns a formatted budget range string.

        :return: str - Formatted budget range
        """
        if self.budgetMin and self.budgetMax:
            return f"${self.budgetMin} - ${self.budgetMax}"
        elif self.budgetMin:
            return f"From ${self.budgetMin}"
        elif self.budgetMax:
            return f"Up to ${self.budgetMax}"
        return "Budget negotiable"

    def getRequiredSkillsList(self):
        """
        Converts required skills string to a list for easier processing.

        :return: list - List of individual required skills
        """
        if self.requiredSkills:
            return [
                skill.strip()
                for skill in self.requiredSkills.split(",")
                if skill.strip()
            ]
        return []

    def isEligibleForRating(self):
        """
        Checks if this job is eligible for rating (completed status).

        :return: bool - True if job can be rated, False otherwise
        """
        return self.status == "completed"

    @classmethod
    def getPostedJobs(cls):
        """
        Retrieves all jobs that are currently posted and accepting applications.

        :return: list - List of posted Job objects
        """
        return cls.query.filter_by(status="posted").all()

    @classmethod
    def getJobsInProgress(cls):
        """
        Retrieves all jobs currently in progress.

        :return: list - List of in-progress Job objects
        """
        return cls.query.filter_by(status="in_progress").all()

    @classmethod
    def getCompletedJobs(cls):
        """
        Retrieves all completed jobs.

        :return: list - List of completed Job objects
        """
        return cls.query.filter_by(status="completed").all()

    @classmethod
    def getJobsByBudgetRange(cls, minBudget: float, maxBudget: float):
        """
        Retrieves posted jobs within a specific budget range.

        :param minBudget: float - Minimum budget threshold
        :param maxBudget: float - Maximum budget threshold
        :return: list - List of Job objects within budget range
        """
        return cls.query.filter(
            cls.status == "posted",
            cls.budgetMin >= minBudget,
            cls.budgetMax <= maxBudget,
        ).all()

    @classmethod
    def getJobsBySkill(cls, skill: str):
        """
        Retrieves posted jobs that require a specific skill.

        :param skill: str - Skill to search for in required skills
        :return: list - List of Job objects requiring the specified skill
        """
        return cls.query.filter(
            cls.status == "posted", cls.requiredSkills.like(f"%{skill}%")
        ).all()

    @classmethod
    def getRecentJobs(cls, limit: int = 10):
        """
        Retrieves the most recently posted jobs.

        :param limit: int - Maximum number of jobs to return
        :return: list - List of recent posted Job objects
        """
        return (
            cls.query.filter_by(status="posted")
            .order_by(cls.dateCreated.desc())
            .limit(limit)
            .all()
        )
