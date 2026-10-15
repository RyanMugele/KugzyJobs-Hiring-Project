from app import db
import json


class Creator(db.Model):
    """
    Model representing a Content Creator in the platform.
    Inherits common user functionality through the User relationship.
    """

    __tablename__ = "creator"

    creatorId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    userId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), unique=True, nullable=False
    )
    contentType = db.Column(db.String(100), nullable=True)
    platformFocus = db.Column(db.String(100), nullable=True)
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
    user = db.relationship("User", back_populates="creator")
    jobs = db.relationship(
        "Job", back_populates="creator", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """
        String representation of the Creator object.

        :return: str - String representation showing creatorId and associated user info
        """
        return f"Creator(creatorId={self.creatorId}, userId={self.userId}, contentType={self.contentType})"

    @property
    def user_type(self):
        """
        Property to specify the type of user for authentication purposes.

        :return: str - The user type
        """
        return self.__tablename__

    def get_id(self) -> int:
        """
        Method used by Flask-Login to retrieve creator id for session management.

        :return: int - Creator ID of the creator
        """
        return self.creatorId

    def updateContentPreferences(
        self, contentType: str = None, platformFocus: str = None
    ):
        """
        Updates the creator's content preferences.

        :param contentType: str - Type of content the creator produces
        :param platformFocus: str - Platform the creator focuses on
        :return: None
        """
        if contentType is not None:
            self.contentType = contentType
        if platformFocus is not None:
            self.platformFocus = platformFocus

        db.session.commit()

    def getActiveJobs(self):
        """
        Retrieves all active jobs posted by this creator.

        :return: list - List of active Job objects
        """
        return [job for job in self.jobs if job.status != "completed"]

    def getCompletedJobs(self):
        """
        Retrieves all completed jobs posted by this creator.

        :return: list - List of completed Job objects
        """
        return [job for job in self.jobs if job.status == "completed"]

    def postJob(self, jobDetails: dict):
        """
        Creates a new job posting for this creator.

        :param jobDetails: dict - Dictionary containing job details
        :return: Job - The newly created Job object
        """
        from .job import Job

        job = Job(
            creatorId=self.creatorId,
            title=jobDetails.get("title"),
            description=jobDetails.get("description"),
            budgetMin=jobDetails.get("budgetMin"),
            budgetMax=jobDetails.get("budgetMax"),
            deadline=jobDetails.get("deadline"),
            requiredSkills=jobDetails.get("requiredSkills"),

            #NLP extracted Information
            extractedSkills=json.dumps(jobDetails.get("extractedSkills", [])),
            extractedStyles=json.dumps(jobDetails.get("extractedStyles", [])),
            extractedNiches=json.dumps(jobDetails.get("extractedNiches", [])),

        )

        db.session.add(job)
        db.session.commit()
        return job

    def selectEditorForJob(self, jobId: int, editorId: int):
        """
        Selects an editor for a specific job and updates job status.

        :param jobId: int - ID of the job
        :param editorId: int - ID of the selected editor
        :return: bool - True if selection was successful, False otherwise
        """
        job = next((j for j in self.jobs if j.jobId == jobId), None)
        if job and job.status == "posted":
            job.selectedEditorId = editorId
            job.status = "in_progress"
            db.session.commit()
            return True
        return False

    def markJobCompleted(self, jobId: int, deliverableUrl: str = None):
        """
        Marks a job as completed and optionally sets deliverable URL.

        :param jobId: int - ID of the job to complete
        :param deliverableUrl: str - URL to the completed deliverable
        :return: bool - True if job was marked completed, False otherwise
        """
        job = next((j for j in self.jobs if j.jobId == jobId), None)
        if job and job.status == "in_progress":
            job.status = "completed"
            job.completedDate = db.func.current_timestamp()
            if deliverableUrl:
                job.deliverableUrl = deliverableUrl
            db.session.commit()
            return True
        return False

    @classmethod
    def getCreatorsByContentType(cls, contentType: str):
        """
        Retrieves creators who specialize in a specific content type.

        :param contentType: str - The content type to filter by
        :return: list - List of Creator objects
        """
        return cls.query.filter_by(contentType=contentType).all()

    @classmethod
    def getCreatorsByPlatform(cls, platform: str):
        """
        Retrieves creators who focus on a specific platform.

        :param platform: str - The platform to filter by
        :return: list - List of Creator objects
        """
        return cls.query.filter_by(platformFocus=platform).all()
