from app import db


class Rating(db.Model):
    """
    Model representing a Rating between users after project completion.
    Handles the mutual rating system between creators and editors.
    """

    __tablename__ = "rating"

    ratingId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    jobId = db.Column(db.Integer, db.ForeignKey("job.jobId"), nullable=False)
    raterId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), nullable=False
    )
    rateeId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), nullable=False
    )
    ratingValue = db.Column(db.Integer, nullable=False)
    reviewText = db.Column(db.Text, nullable=True)
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
    job = db.relationship("Job", back_populates="ratings")
    rater = db.relationship(
        "User", foreign_keys=[raterId], back_populates="givenRatings"
    )
    ratee = db.relationship(
        "User", foreign_keys=[rateeId], back_populates="receivedRatings"
    )

    # Constraints
    __table_args__ = (
        db.CheckConstraint(
            "ratingValue >= 1 AND ratingValue <= 5", name="valid_rating_range"
        ),
        db.UniqueConstraint(
            "jobId", "raterId", "rateeId", name="unique_job_rating"
        ),
    )

    def __repr__(self) -> str:
        """
        String representation of the Rating object.

        :return: str - String representation showing rating details
        """
        return f"Rating(ratingId={self.ratingId}, jobId={self.jobId}, rating={self.ratingValue}/5)"

    def updateRating(self, ratingValue: int = None, reviewText: str = None):
        """
        Updates the rating details (value and review text).

        :param ratingValue: int - New rating value (1-5)
        :param reviewText: str - New review text
        :return: bool - True if update was successful, False otherwise
        """
        if ratingValue is not None:
            if 1 <= ratingValue <= 5:
                self.ratingValue = ratingValue
            else:
                return False

        if reviewText is not None:
            self.reviewText = reviewText

        db.session.commit()

        # Update the ratee's average rating
        self.ratee.updateAverageRating()

        return True

    def deleteRating(self):
        """
        Deletes this rating and updates the ratee's average rating.

        :return: None
        """
        ratee = self.ratee
        db.session.delete(self)
        db.session.commit()

        # Update the ratee's average rating after deletion
        ratee.updateAverageRating()

    def isPositive(self):
        """
        Checks if this is a positive rating (4-5 stars).

        :return: bool - True if rating is 4 or 5 stars
        """
        return self.ratingValue >= 4

    def isNegative(self):
        """
        Checks if this is a negative rating (1-2 stars).

        :return: bool - True if rating is 1 or 2 stars
        """
        return self.ratingValue <= 2

    def isNeutral(self):
        """
        Checks if this is a neutral rating (3 stars).

        :return: bool - True if rating is exactly 3 stars
        """
        return self.ratingValue == 3

    def getRatingCategory(self):
        """
        Returns the category of this rating.

        :return: str - Category of the rating ('excellent', 'good', 'neutral', 'poor', 'terrible')
        """
        categories = {
            5: "excellent",
            4: "good",
            3: "neutral",
            2: "poor",
            1: "terrible",
        }
        return categories.get(self.ratingValue, "unknown")

    def getStarDisplay(self):
        """
        Returns a star representation of the rating.

        :return: str - Star representation (e.g., "★★★★☆")
        """
        filled_stars = "★" * self.ratingValue
        empty_stars = "☆" * (5 - self.ratingValue)
        return filled_stars + empty_stars

    def getRatingDetails(self):
        """
        Returns comprehensive rating details for display.

        :return: dict - Dictionary containing rating information
        """
        return {
            "rating_id": self.ratingId,
            "job_id": self.jobId,
            "job_title": self.job.title if self.job else "Unknown",
            "rater_name": self.rater.fullName if self.rater else "Unknown",
            "ratee_name": self.ratee.fullName if self.ratee else "Unknown",
            "rating_value": self.ratingValue,
            "rating_category": self.getRatingCategory(),
            "star_display": self.getStarDisplay(),
            "review_text": self.reviewText,
            "has_review": bool(self.reviewText),
            "created_date": self.dateCreated.strftime("%Y-%m-%d"),
            "is_positive": self.isPositive(),
            "is_negative": self.isNegative(),
        }

    @classmethod
    def createRating(
        cls,
        jobId: int,
        raterId: int,
        rateeId: int,
        ratingValue: int,
        reviewText: str = None,
    ):
        """
        Creates a new rating between users for a completed job.

        :param jobId: int - ID of the completed job
        :param raterId: int - ID of the user giving the rating
        :param rateeId: int - ID of the user receiving the rating
        :param ratingValue: int - Rating value (1-5)
        :param reviewText: str - Optional review text
        :return: Rating|None - Created Rating object or None if validation fails
        """
        # Validate rating value
        if not (1 <= ratingValue <= 5):
            return None

        # Check if rating already exists
        existing_rating = cls.query.filter_by(
            jobId=jobId, raterId=raterId, rateeId=rateeId
        ).first()
        if existing_rating:
            return None

        # Verify job is completed
        from .job import Job

        job = Job.query.get(jobId)
        if not job or job.status != "completed":
            return None

        # Create the rating
        rating = cls(
            jobId=jobId,
            raterId=raterId,
            rateeId=rateeId,
            ratingValue=ratingValue,
            reviewText=reviewText,
        )

        db.session.add(rating)
        db.session.commit()

        # Update ratee's average rating
        from .user import User

        ratee = User.query.get(rateeId)
        if ratee:
            ratee.updateAverageRating()

        return rating

    @classmethod
    def getRatingsForUser(cls, userId: int):
        """
        Retrieves all ratings received by a specific user.

        :param userId: int - ID of the user
        :return: list - List of Rating objects received by the user
        """
        return cls.query.filter_by(rateeId=userId).all()

    @classmethod
    def getRatingsByUser(cls, userId: int):
        """
        Retrieves all ratings given by a specific user.

        :param userId: int - ID of the user
        :return: list - List of Rating objects given by the user
        """
        return cls.query.filter_by(raterId=userId).all()

    @classmethod
    def getRatingsForJob(cls, jobId: int):
        """
        Retrieves all ratings for a specific job.

        :param jobId: int - ID of the job
        :return: list - List of Rating objects for the job
        """
        return cls.query.filter_by(jobId=jobId).all()

    @classmethod
    def getHighRatings(cls, minRating: int = 4):
        """
        Retrieves all ratings above a certain threshold.

        :param minRating: int - Minimum rating value to filter by
        :return: list - List of high Rating objects
        """
        return cls.query.filter(cls.ratingValue >= minRating).all()

    @classmethod
    def getLowRatings(cls, maxRating: int = 2):
        """
        Retrieves all ratings below a certain threshold.

        :param maxRating: int - Maximum rating value to filter by
        :return: list - List of low Rating objects
        """
        return cls.query.filter(cls.ratingValue <= maxRating).all()

    @classmethod
    def getRecentRatings(cls, limit: int = 10):
        """
        Retrieves the most recently submitted ratings.

        :param limit: int - Maximum number of ratings to return
        :return: list - List of recent Rating objects
        """
        return cls.query.order_by(cls.dateCreated.desc()).limit(limit).all()

    @classmethod
    def getRatingStatistics(cls):
        """
        Generates comprehensive rating statistics for the platform.

        :return: dict - Dictionary containing rating statistics
        """
        total_ratings = cls.query.count()

        if total_ratings == 0:
            return {
                "total_ratings": 0,
                "average_rating": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "positive_percentage": 0,
                "negative_percentage": 0,
            }

        # Calculate average rating
        avg_result = db.session.query(db.func.avg(cls.ratingValue)).scalar()
        average_rating = round(float(avg_result), 2) if avg_result else 0

        # Rating distribution
        distribution = {}
        for i in range(1, 6):
            count = cls.query.filter_by(ratingValue=i).count()
            distribution[i] = count

        # Positive and negative percentages
        positive_count = cls.query.filter(cls.ratingValue >= 4).count()
        negative_count = cls.query.filter(cls.ratingValue <= 2).count()

        positive_percentage = round((positive_count / total_ratings * 100), 2)
        negative_percentage = round((negative_count / total_ratings * 100), 2)

        return {
            "total_ratings": total_ratings,
            "average_rating": average_rating,
            "rating_distribution": distribution,
            "positive_percentage": positive_percentage,
            "negative_percentage": negative_percentage,
            "neutral_percentage": round(
                100 - positive_percentage - negative_percentage, 2
            ),
        }

    @classmethod
    def checkExistingRating(cls, jobId: int, raterId: int, rateeId: int):
        """
        Checks if a rating already exists for the given parameters.

        :param jobId: int - ID of the job
        :param raterId: int - ID of the rater
        :param rateeId: int - ID of the ratee
        :return: Rating|None - Existing rating or None
        """
        return cls.query.filter_by(
            jobId=jobId, raterId=raterId, rateeId=rateeId
        ).first()
