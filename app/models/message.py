from app import db


class Message(db.Model):
    """
    Model representing a Message between platform users.
    Supports email-based communication with logging for reference.
    """

    __tablename__ = "message"

    messageId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    jobId = db.Column(db.Integer, db.ForeignKey("job.jobId"), nullable=True)
    senderId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), nullable=False
    )
    receiverId = db.Column(
        db.Integer, db.ForeignKey("user.userId"), nullable=False
    )
    subject = db.Column(db.String(200), nullable=True)
    messageContent = db.Column(db.Text, nullable=False)
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
    job = db.relationship("Job", back_populates="messages")
    sender = db.relationship(
        "User", foreign_keys=[senderId], back_populates="sentMessages"
    )
    receiver = db.relationship(
        "User", foreign_keys=[receiverId], back_populates="receivedMessages"
    )

    def __repr__(self) -> str:
        """
        String representation of the Message object.

        :return: str - String representation showing message details
        """
        return f"Message(messageId={self.messageId}, subject={self.subject}, senderId={self.senderId})"

    def getMessageSummary(self):
        """
        Returns a summary of the message for display in message lists.

        :return: dict - Dictionary containing message summary
        """
        return {
            "message_id": self.messageId,
            "subject": self.subject or "No Subject",
            "sender_name": self.sender.fullName if self.sender else "Unknown",
            "receiver_name": self.receiver.fullName
            if self.receiver
            else "Unknown",
            "content_preview": self.messageContent[:100] + "..."
            if len(self.messageContent) > 100
            else self.messageContent,
            "content_length": len(self.messageContent),
            "job_title": self.job.title if self.job else None,
            "job_id": self.jobId,
            "sent_date": self.dateCreated.strftime("%Y-%m-%d %H:%M"),
            "is_job_related": bool(self.jobId),
        }

    def getFullMessageDetails(self):
        """
        Returns complete message details for viewing.

        :return: dict - Dictionary containing full message information
        """
        return {
            "message_id": self.messageId,
            "subject": self.subject,
            "sender_name": self.sender.fullName if self.sender else "Unknown",
            "sender_email": self.sender.emailAddress
            if self.sender
            else "Unknown",
            "receiver_name": self.receiver.fullName
            if self.receiver
            else "Unknown",
            "receiver_email": self.receiver.emailAddress
            if self.receiver
            else "Unknown",
            "content": self.messageContent,
            "job_title": self.job.title if self.job else None,
            "job_id": self.jobId,
            "sent_date": self.dateCreated.strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": self.lastUpdated.strftime("%Y-%m-%d %H:%M:%S"),
            "is_job_related": bool(self.jobId),
        }

    def isJobRelated(self):
        """
        Checks if this message is related to a specific job.

        :return: bool - True if message is job-related, False otherwise
        """
        return bool(self.jobId)

    def getJobContext(self):
        """
        Returns job context information if message is job-related.

        :return: dict|None - Job context or None if not job-related
        """
        if self.job:
            return {
                "job_id": self.job.jobId,
                "job_title": self.job.title,
                "job_status": self.job.status,
                "creator_name": self.job.creator.user.fullName
                if self.job.creator and self.job.creator.user
                else "Unknown",
                "selected_editor_name": self.job.selectedEditor.user.fullName
                if self.job.selectedEditor and self.job.selectedEditor.user
                else None,
            }
        return None

    def replyTo(self, replyContent: str, replySubject: str = None):
        """
        Creates a reply message to this message.

        :param replyContent: str - Content of the reply message
        :param replySubject: str - Subject of the reply (auto-generated if not provided)
        :return: Message - The created reply message
        """
        if not replySubject:
            original_subject = self.subject or "No Subject"
            replySubject = (
                f"Re: {original_subject}"
                if not original_subject.startswith("Re:")
                else original_subject
            )

        reply = Message(
            jobId=self.jobId,  # Keep same job context
            senderId=self.receiverId,  # Receiver becomes sender
            receiverId=self.senderId,  # Sender becomes receiver
            subject=replySubject,
            messageContent=replyContent,
        )

        db.session.add(reply)
        db.session.commit()
        return reply

    @classmethod
    def sendMessage(
        cls,
        senderId: int,
        receiverId: int,
        messageContent: str,
        subject: str = None,
        jobId: int = None,
    ):
        """
        Sends a new message between users.

        :param senderId: int - ID of the user sending the message
        :param receiverId: int - ID of the user receiving the message
        :param messageContent: str - Content of the message
        :param subject: str - Subject of the message
        :param jobId: int - Optional job ID for job-related messages
        :return: Message - The created Message object
        """
        message = cls(
            senderId=senderId,
            receiverId=receiverId,
            messageContent=messageContent,
            subject=subject,
            jobId=jobId,
        )

        db.session.add(message)
        db.session.commit()
        return message

    @classmethod
    def getMessagesForUser(cls, userId: int, messageType: str = "all"):
        """
        Retrieves messages for a specific user.

        :param userId: int - ID of the user
        :param messageType: str - Type of messages ('sent', 'received', 'all')
        :return: list - List of Message objects
        """
        if messageType == "sent":
            return (
                cls.query.filter_by(senderId=userId)
                .order_by(cls.dateCreated.desc())
                .all()
            )
        elif messageType == "received":
            return (
                cls.query.filter_by(receiverId=userId)
                .order_by(cls.dateCreated.desc())
                .all()
            )
        else:  # all
            return (
                cls.query.filter(
                    (cls.senderId == userId) | (cls.receiverId == userId)
                )
                .order_by(cls.dateCreated.desc())
                .all()
            )

    @classmethod
    def getConversation(cls, user1Id: int, user2Id: int, jobId: int = None):
        """
        Retrieves all messages in a conversation between two users.

        :param user1Id: int - ID of the first user
        :param user2Id: int - ID of the second user
        :param jobId: int - Optional job ID to filter job-related messages
        :return: list - List of Message objects in chronological order
        """
        query = cls.query.filter(
            ((cls.senderId == user1Id) & (cls.receiverId == user2Id))
            | ((cls.senderId == user2Id) & (cls.receiverId == user1Id))
        )

        if jobId:
            query = query.filter_by(jobId=jobId)

        return query.order_by(cls.dateCreated.asc()).all()

    @classmethod
    def getJobMessages(cls, jobId: int):
        """
        Retrieves all messages related to a specific job.

        :param jobId: int - ID of the job
        :return: list - List of job-related Message objects
        """
        return (
            cls.query.filter_by(jobId=jobId)
            .order_by(cls.dateCreated.asc())
            .all()
        )

    @classmethod
    def getRecentMessages(cls, limit: int = 10):
        """
        Retrieves the most recent messages across the platform.

        :param limit: int - Maximum number of messages to return
        :return: list - List of recent Message objects
        """
        return cls.query.order_by(cls.dateCreated.desc()).limit(limit).all()

    @classmethod
    def searchMessages(cls, userId: int, searchTerm: str):
        """
        Searches messages for a user by content or subject.

        :param userId: int - ID of the user whose messages to search
        :param searchTerm: str - Term to search for
        :return: list - List of matching Message objects
        """
        return (
            cls.query.filter(
                ((cls.senderId == userId) | (cls.receiverId == userId))
                & (
                    (cls.subject.like(f"%{searchTerm}%"))
                    | (cls.messageContent.like(f"%{searchTerm}%"))
                )
            )
            .order_by(cls.dateCreated.desc())
            .all()
        )

    @classmethod
    def getMessageStatistics(cls):
        """
        Generates message statistics for the platform.

        :return: dict - Dictionary containing message statistics
        """
        total_messages = cls.query.count()
        job_related_messages = cls.query.filter(cls.jobId.isnot(None)).count()
        general_messages = total_messages - job_related_messages

        # Recent activity (last 7 days)
        from datetime import datetime
        from datetime import timedelta

        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_messages = cls.query.filter(cls.dateCreated >= week_ago).count()

        return {
            "total_messages": total_messages,
            "job_related_messages": job_related_messages,
            "general_messages": general_messages,
            "recent_messages": recent_messages,
            "job_related_percentage": round(
                (job_related_messages / total_messages * 100)
                if total_messages > 0
                else 0,
                2,
            ),
        }

    @classmethod
    def getActiveConversations(cls, userId: int, limit: int = 10):
        """
        Retrieves the most recent conversations for a user.

        :param userId: int - ID of the user
        :param limit: int - Maximum number of conversations to return
        :return: list - List of dictionaries containing conversation information
        """
        # Get unique conversation partners with their latest messages
        subquery = (
            db.session.query(
                db.case(
                    (cls.senderId == userId, cls.receiverId), else_=cls.senderId
                ).label("partner_id"),
                db.func.max(cls.dateCreated).label("latest_message_date"),
            )
            .filter((cls.senderId == userId) | (cls.receiverId == userId))
            .group_by("partner_id")
            .subquery()
        )

        # Get the actual latest messages
        latest_messages = (
            db.session.query(cls)
            .join(
                subquery,
                (cls.dateCreated == subquery.c.latest_message_date)
                & (
                    (
                        (cls.senderId == userId)
                        & (cls.receiverId == subquery.c.partner_id)
                    )
                    | (
                        (cls.receiverId == userId)
                        & (cls.senderId == subquery.c.partner_id)
                    )
                ),
            )
            .order_by(cls.dateCreated.desc())
            .limit(limit)
            .all()
        )

        conversations = []
        for message in latest_messages:
            partner_id = (
                message.receiverId
                if message.senderId == userId
                else message.senderId
            )
            partner = (
                message.receiver
                if message.senderId == userId
                else message.sender
            )

            conversations.append(
                {
                    "partner_id": partner_id,
                    "partner_name": partner.fullName if partner else "Unknown",
                    "latest_message": message.getMessageSummary(),
                    "message_count": cls.getConversation(
                        userId, partner_id
                    ).__len__(),
                }
            )

        return conversations
