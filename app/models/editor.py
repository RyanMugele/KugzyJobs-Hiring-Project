from app import db


class Editor(db.Model):
    """
    Model representing a Video Editor in the platform.
    Inherits common user functionality through the User relationship.
    """

    __tablename__ = "editor"

    editorId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    userId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), unique=True, nullable=False
    )
    specializations = db.Column(db.Text, nullable=True)
    experienceLevel = db.Column(db.String(50), nullable=True)
    hourlyRate = db.Column(db.Numeric(10, 2), nullable=True)
    isVerified = db.Column(db.Boolean, default=False, nullable=False)
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
    user = db.relationship("User", back_populates="editor")
    portfolios = db.relationship(
        "Portfolio", back_populates="editor", cascade="all, delete-orphan"
    )
    jobApplications = db.relationship(
        "JobApplication", back_populates="editor", cascade="all, delete-orphan"
    )
    selectedJobs = db.relationship(
        "Job",
        foreign_keys="Job.selectedEditorId",
        back_populates="selectedEditor",
    )

    def __repr__(self) -> str:
        """
        String representation of the Editor object.

        :return: str - String representation showing editorId and associated user info
        """
        return f"Editor(editorId={self.editorId}, userId={self.userId}, isVerified={self.isVerified})"

    @property
    def user_type(self):
        """
        Property to specify the type of user for authentication purposes.

        :return: str - The user type
        """
        return self.__tablename__

    def get_id(self) -> int:
        """
        Method used by Flask-Login to retrieve editor id for session management.

        :return: int - Editor ID of the editor
        """
        return self.editorId

    def updateSpecializationsAndRates(
        self,
        specializations: str = None,
        hourlyRate: float = None,
        experienceLevel: str = None,
    ):
        """
        Updates the editor's specializations, rates, and experience level.

        :param specializations: str - Editor's areas of expertise
        :param hourlyRate: float - Editor's hourly rate
        :param experienceLevel: str - Editor's experience level
        :return: None
        """
        if specializations is not None:
            self.specializations = specializations
        if hourlyRate is not None:
            self.hourlyRate = hourlyRate
        if experienceLevel is not None:
            self.experienceLevel = experienceLevel

        db.session.commit()

    def addPortfolioItem(self, portfolioDetails: dict):
        """
        Adds a new portfolio item for this editor.

        :param portfolioDetails: dict - Dictionary containing portfolio details
        :return: Portfolio - The newly created Portfolio object
        """
        from .portfolio import Portfolio

        portfolio = Portfolio(
            editorId=self.editorId,
            title=portfolioDetails.get("title"),
            description=portfolioDetails.get("description"),
            videoUrl=portfolioDetails.get("videoUrl"),
            skillTags=portfolioDetails.get("skillTags"),
        )

        db.session.add(portfolio)
        db.session.commit()
        return portfolio

    def getVerifiedPortfolios(self):
        """
        Retrieves all verified portfolio items for this editor.

        :return: list - List of verified Portfolio objects
        """
        return [
            portfolio
            for portfolio in self.portfolios
            if portfolio.verificationStatus == "approved"
        ]

    def getPendingPortfolios(self):
        """
        Retrieves all pending portfolio items for this editor.

        :return: list - List of pending Portfolio objects
        """
        return [
            portfolio
            for portfolio in self.portfolios
            if portfolio.verificationStatus == "pending"
        ]

    def applyForJob(self, jobId: int, applicationDetails: dict):
        """
        Submits an application for a specific job.

        :param jobId: int - ID of the job to apply for
        :param applicationDetails: dict - Application details including rate and proposal
        :return: JobApplication - The newly created JobApplication object
        """
        from .job_application import JobApplication

        application = JobApplication(
            jobId=jobId,
            editorId=self.editorId,
            proposedRate=applicationDetails.get("proposedRate"),
            proposedTimeline=applicationDetails.get("proposedTimeline"),
            customProposal=applicationDetails.get("customProposal"),
        )

        db.session.add(application)
        db.session.commit()
        return application

    def getActiveApplications(self):
        """
        Retrieves all pending job applications for this editor.

        :return: list - List of pending JobApplication objects
        """
        return [app for app in self.jobApplications if app.status == "pending"]

    def getAcceptedApplications(self):
        """
        Retrieves all accepted job applications for this editor.

        :return: list - List of accepted JobApplication objects
        """
        return [app for app in self.jobApplications if app.status == "accepted"]

    def getCurrentJobs(self):
        """
        Retrieves all jobs currently assigned to this editor.

        :return: list - List of Job objects in progress
        """
        return [job for job in self.selectedJobs if job.status == "in_progress"]

    def getCompletedJobs(self):
        """
        Retrieves all jobs completed by this editor.

        :return: list - List of completed Job objects
        """
        return [job for job in self.selectedJobs if job.status == "completed"]

    def uploadDeliverable(self, jobId: int, deliverableUrl: str):
        """
        Uploads a deliverable for a completed job.

        :param jobId: int - ID of the job
        :param deliverableUrl: str - URL to the deliverable file
        :return: bool - True if upload was successful, False otherwise
        """
        job = next((j for j in self.selectedJobs if j.jobId == jobId), None)
        if job and job.status == "in_progress":
            job.deliverableUrl = deliverableUrl
            db.session.commit()
            return True
        return False

    @classmethod
    def getVerifiedEditors(cls):
        """
        Retrieves all verified editors in the platform.

        :return: list - List of verified Editor objects
        """
        return cls.query.filter_by(isVerified=True).all()

    @classmethod
    def getEditorsByExperienceLevel(cls, experienceLevel: str):
        """
        Retrieves editors by their experience level.

        :param experienceLevel: str - The experience level to filter by
        :return: list - List of Editor objects
        """
        return cls.query.filter_by(experienceLevel=experienceLevel).all()

    @classmethod
    def getEditorsBySpecialization(cls, specialization: str):
        """
        Retrieves editors who have a specific specialization.

        :param specialization: str - The specialization to search for
        :return: list - List of Editor objects
        """
        return cls.query.filter(
            cls.specializations.like(f"%{specialization}%")
        ).all()

    @classmethod
    def getEditorsWithinBudget(cls, maxBudget: float):
        """
        Retrieves editors whose hourly rate is within the specified budget.

        :param maxBudget: float - Maximum hourly rate budget
        :return: list - List of Editor objects
        """
        return cls.query.filter(cls.hourlyRate <= maxBudget).all()
