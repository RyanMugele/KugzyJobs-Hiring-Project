from app import db


class PasswordResetToken(db.Model):
    """
    Model representing a Password Reset Token for secure password recovery.
    Implements Werkzeug-based token generation for secure password reset functionality.
    """

    __tablename__ = "password_reset_token"

    tokenId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("user.userId"), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expiresAt = db.Column(db.TIMESTAMP, nullable=False)
    isUsed = db.Column(db.Boolean, default=False, nullable=False)
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
    user = db.relationship("User", back_populates="passwordResetTokens")

    def __repr__(self) -> str:
        """
        String representation of the PasswordResetToken object.

        :return: str - String representation showing token details
        """
        return f"PasswordResetToken(tokenId={self.tokenId}, userId={self.userId}, isUsed={self.isUsed})"

    def isValid(self):
        """
        Checks if the token is still valid (not expired and not used).

        :return: bool - True if token is valid, False otherwise
        """
        from datetime import datetime

        if self.isUsed:
            return False

        if datetime.utcnow() > self.expiresAt:
            return False

        return True

    def isExpired(self):
        """
        Checks if the token has expired.

        :return: bool - True if token is expired, False otherwise
        """
        from datetime import datetime

        return datetime.utcnow() > self.expiresAt

    def markAsUsed(self):
        """
        Marks the token as used to prevent reuse.

        :return: None
        """
        self.isUsed = True
        db.session.commit()

    def invalidateToken(self):
        """
        Invalidates the token by marking it as used.

        :return: None
        """
        self.markAsUsed()

    def getTokenInfo(self):
        """
        Returns comprehensive token information for validation.

        :return: dict - Dictionary containing token information
        """
        from datetime import datetime

        time_remaining = None
        if not self.isExpired():
            time_remaining = (
                self.expiresAt - datetime.utcnow()
            ).total_seconds() / 3600  # hours

        return {
            "token_id": self.tokenId,
            "user_id": self.userId,
            "user_name": self.user.fullName if self.user else "Unknown",
            "user_email": self.user.emailAddress if self.user else "Unknown",
            "token": self.token,
            "is_valid": self.isValid(),
            "is_used": self.isUsed,
            "is_expired": self.isExpired(),
            "expires_at": self.expiresAt.strftime("%Y-%m-%d %H:%M:%S"),
            "created_date": self.dateCreated.strftime("%Y-%m-%d %H:%M:%S"),
            "hours_remaining": round(time_remaining, 2)
            if time_remaining and time_remaining > 0
            else 0,
        }

    def extendExpiry(self, hours: int = 24):
        """
        Extends the token expiry time (only if not already used).

        :param hours: int - Number of hours to extend the expiry
        :return: bool - True if extension was successful, False otherwise
        """
        if self.isUsed:
            return False

        from datetime import datetime
        from datetime import timedelta

        self.expiresAt = datetime.utcnow() + timedelta(hours=hours)
        db.session.commit()
        return True

    @classmethod
    def generateToken(cls, userId: int, expiryHours: int = 24):
        """
        Generates a new password reset token for a user using Werkzeug.

        :param userId: int - ID of the user requesting password reset
        :param expiryHours: int - Number of hours until token expires
        :return: PasswordResetToken - The created token object
        """
        from datetime import datetime
        from datetime import timedelta
        from werkzeug.security import generate_password_hash
        import uuid

        # Invalidate any existing tokens for this user
        cls.invalidateUserTokens(userId)

        # Generate secure token using Werkzeug pattern
        token_data = f"{userId}-{uuid.uuid4()}-{datetime.utcnow().timestamp()}"
        secure_token = generate_password_hash(token_data)

        # Create clean token (remove hash prefix for URL usage)
        clean_token = secure_token.replace("pbkdf2:sha256:", "").replace(
            "$", "-"
        )[:64]

        expiry_time = datetime.utcnow() + timedelta(hours=expiryHours)

        reset_token = cls(
            userId=userId, token=clean_token, expiresAt=expiry_time
        )

        db.session.add(reset_token)
        db.session.commit()
        return reset_token

    @classmethod
    def validateToken(cls, token: str):
        """
        Validates a password reset token.

        :param token: str - Token string to validate
        :return: PasswordResetToken|None - Valid token object or None
        """
        reset_token = cls.query.filter_by(token=token).first()

        if reset_token and reset_token.isValid():
            return reset_token

        return None

    @classmethod
    def findByToken(cls, token: str):
        """
        Finds a password reset token by token string.

        :param token: str - Token string to search for
        :return: PasswordResetToken|None - Found token or None
        """
        return cls.query.filter_by(token=token).first()

    @classmethod
    def findValidTokenForUser(cls, userId: int):
        """
        Finds a valid (unexpired, unused) token for a specific user.

        :param userId: int - ID of the user
        :return: PasswordResetToken|None - Valid token or None
        """
        from datetime import datetime

        return cls.query.filter(
            cls.userId == userId,
            cls.isUsed == False,
            cls.expiresAt > datetime.utcnow(),
        ).first()

    @classmethod
    def invalidateUserTokens(cls, userId: int):
        """
        Invalidates all existing tokens for a user.

        :param userId: int - ID of the user
        :return: int - Number of tokens invalidated
        """
        tokens = cls.query.filter_by(userId=userId, isUsed=False).all()
        count = 0

        for token in tokens:
            token.markAsUsed()
            count += 1

        return count

    @classmethod
    def cleanupExpiredTokens(cls):
        """
        Removes all expired tokens from the database.

        :return: int - Number of tokens removed
        """
        from datetime import datetime

        expired_tokens = cls.query.filter(
            cls.expiresAt < datetime.utcnow()
        ).all()

        count = len(expired_tokens)

        for token in expired_tokens:
            db.session.delete(token)

        db.session.commit()
        return count

    @classmethod
    def getTokenStatistics(cls):
        """
        Generates statistics about password reset tokens.

        :return: dict - Dictionary containing token statistics
        """
        from datetime import datetime
        from datetime import timedelta

        total_tokens = cls.query.count()
        used_tokens = cls.query.filter_by(isUsed=True).count()
        expired_tokens = cls.query.filter(
            cls.expiresAt < datetime.utcnow()
        ).count()
        valid_tokens = cls.query.filter(
            cls.isUsed == False, cls.expiresAt > datetime.utcnow()
        ).count()

        # Recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_tokens = cls.query.filter(
            cls.dateCreated >= recent_cutoff
        ).count()

        usage_rate = round(
            (used_tokens / total_tokens * 100) if total_tokens > 0 else 0, 2
        )

        return {
            "total_tokens": total_tokens,
            "used_tokens": used_tokens,
            "expired_tokens": expired_tokens,
            "valid_tokens": valid_tokens,
            "recent_tokens_24h": recent_tokens,
            "usage_rate_percentage": usage_rate,
            "cleanup_candidates": expired_tokens,
        }

    @classmethod
    def getUserTokenHistory(cls, userId: int, limit: int = 10):
        """
        Retrieves password reset token history for a user.

        :param userId: int - ID of the user
        :param limit: int - Maximum number of tokens to return
        :return: list - List of PasswordResetToken objects for the user
        """
        return (
            cls.query.filter_by(userId=userId)
            .order_by(cls.dateCreated.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def getRecentTokenActivity(cls, hours: int = 24, limit: int = 20):
        """
        Retrieves recent token generation activity.

        :param hours: int - Number of hours to look back
        :param limit: int - Maximum number of tokens to return
        :return: list - List of recent PasswordResetToken objects
        """
        from datetime import datetime
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return (
            cls.query.filter(cls.dateCreated >= cutoff_time)
            .order_by(cls.dateCreated.desc())
            .limit(limit)
            .all()
        )
