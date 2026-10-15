from app import db


class Portfolio(db.Model):
    """
    Model representing a Portfolio item for video editors.
    Stores editor's work samples that require admin verification before being visible to creators.
    """

    __tablename__ = "portfolio"

    portfolioId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    editorId = db.Column(
        db.Integer, db.ForeignKey("editor.editorId"), nullable=False
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    videoUrl = db.Column(db.String(500), nullable=True)
    skillTags = db.Column(db.Text, nullable=True)
    verificationStatus = db.Column(
        db.Enum("pending", "approved", "rejected"),
        default="pending",
        nullable=False,
    )
    rejectionReason = db.Column(db.Text, nullable=True)
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
    editor = db.relationship("Editor", back_populates="portfolios")
    reports = db.relationship(
        "Report",
        foreign_keys="Report.reportedPortfolioId",
        back_populates="reportedPortfolio",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """
        String representation of the Portfolio object.

        :return: str - String representation showing portfolioId, title and verification status
        """
        return f"Portfolio(portfolioId={self.portfolioId}, title={self.title}, status={self.verificationStatus})"

    def updatePortfolioDetails(
        self, title: str = None, description: str = None, skillTags: str = None
    ):
        """
        Updates portfolio item details.

        :param title: str - New title for the portfolio item
        :param description: str - New description for the portfolio item
        :param skillTags: str - Updated skill tags
        :return: None
        """
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if skillTags is not None:
            self.skillTags = skillTags

        db.session.commit()

    def uploadVideoFile(self, videoUrl: str):
        """
        Updates the video URL for this portfolio item.

        :param videoUrl: str - URL or path to the uploaded video file
        :return: None
        """
        self.videoUrl = videoUrl
        db.session.commit()

    def submitForVerification(self):
        """
        Submits the portfolio item for admin verification.
        Resets status to pending if it was previously rejected.

        :return: None
        """
        self.verificationStatus = "pending"
        self.rejectionReason = None
        db.session.commit()

    def isVisible(self):
        """
        Checks if this portfolio item should be visible to creators.

        :return: bool - True if portfolio is approved and should be visible
        """
        return self.verificationStatus == "approved"

    def getSkillTagsList(self):
        """
        Converts skill tags string to a list for easier processing.

        :return: list - List of individual skill tags
        """
        if self.skillTags:
            return [
                tag.strip() for tag in self.skillTags.split(",") if tag.strip()
            ]
        return []

    def addSkillTag(self, newTag: str):
        """
        Adds a new skill tag to the portfolio item.

        :param newTag: str - New skill tag to add
        :return: None
        """
        current_tags = self.getSkillTagsList()
        if newTag not in current_tags:
            current_tags.append(newTag)
            self.skillTags = ", ".join(current_tags)
            db.session.commit()

    def removeSkillTag(self, tagToRemove: str):
        """
        Removes a skill tag from the portfolio item.

        :param tagToRemove: str - Skill tag to remove
        :return: None
        """
        current_tags = self.getSkillTagsList()
        if tagToRemove in current_tags:
            current_tags.remove(tagToRemove)
            self.skillTags = ", ".join(current_tags)
            db.session.commit()

    @classmethod
    def getApprovedPortfolios(cls):
        """
        Retrieves all approved portfolio items visible to creators.

        :return: list - List of approved Portfolio objects
        """
        return cls.query.filter_by(verificationStatus="approved").all()

    @classmethod
    def getPendingPortfolios(cls):
        """
        Retrieves all portfolio items pending admin verification.

        :return: list - List of pending Portfolio objects
        """
        return cls.query.filter_by(verificationStatus="pending").all()

    @classmethod
    def getPortfoliosBySkill(cls, skill: str):
        """
        Retrieves approved portfolios that demonstrate a specific skill.

        :param skill: str - Skill to search for in skill tags
        :return: list - List of Portfolio objects containing the specified skill
        """
        return cls.query.filter(
            cls.verificationStatus == "approved",
            cls.skillTags.like(f"%{skill}%"),
        ).all()

    @classmethod
    def getRecentPortfolios(cls, limit: int = 10):
        """
        Retrieves the most recently approved portfolio items.

        :param limit: int - Maximum number of portfolios to return
        :return: list - List of recent approved Portfolio objects
        """
        return (
            cls.query.filter_by(verificationStatus="approved")
            .order_by(cls.dateCreated.desc())
            .limit(limit)
            .all()
        )
