from app import db


class PaymentInterim(db.Model):
    """
    Model representing interim payment data for Pesapal integration.
    Critical for handling payment gateway processing and callbacks.
    """

    __tablename__ = "payment_interim"

    paymentInterimId = db.Column(
        db.Integer, autoincrement=True, primary_key=True
    )
    paymentId = db.Column(
        db.Integer, db.ForeignKey("payment.paymentId"), nullable=False
    )
    orderTrackingId = db.Column(db.String(255), nullable=False)
    merchantReference = db.Column(db.String(255), nullable=False)
    iframeSrc = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.Enum("SAVED", "COMPLETED", "FAILED"), default="SAVED", nullable=False
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
    payment = db.relationship("Payment", back_populates="paymentInterim")

    def __repr__(self) -> str:
        """
        String representation of the PaymentInterim object.

        :return: str - String representation showing interim ID and status
        """
        return f"PaymentInterim(paymentInterimId={self.paymentInterimId}, orderTrackingId={self.orderTrackingId}, status={self.status})"

    def updateIframeSrc(self, iframeSrc: str):
        """
        Updates the iframe source URL from payment gateway response.

        :param iframeSrc: str - Payment gateway iframe URL
        :return: None
        """
        self.iframeSrc = iframeSrc
        db.session.commit()

    def markAsCompleted(self, updatePayment: bool = True):
        """
        Marks the interim payment as completed and optionally updates main payment.

        :param updatePayment: bool - Whether to update the main payment status
        :return: None
        """
        self.status = "COMPLETED"

        if updatePayment and self.payment:
            self.payment.updatePaymentStatus("paid")

        db.session.commit()

    def markAsFailed(self):
        """
        Marks the interim payment as failed.

        :return: None
        """
        self.status = "FAILED"
        db.session.commit()

    def isProcessing(self):
        """
        Checks if the payment is currently being processed.

        :return: bool - True if payment is in SAVED status (processing)
        """
        return self.status == "SAVED"

    def isCompleted(self):
        """
        Checks if the payment processing completed successfully.

        :return: bool - True if payment is in COMPLETED status
        """
        return self.status == "COMPLETED"

    def hasFailed(self):
        """
        Checks if the payment processing failed.

        :return: bool - True if payment is in FAILED status
        """
        return self.status == "FAILED"

    def getPaymentInfo(self):
        """
        Returns comprehensive payment information for gateway integration.

        :return: dict - Dictionary containing payment gateway information
        """
        return {
            "interim_id": self.paymentInterimId,
            "payment_id": self.paymentId,
            "order_tracking_id": self.orderTrackingId,
            "merchant_reference": self.merchantReference,
            "iframe_src": self.iframeSrc,
            "status": self.status,
            "amount": float(self.payment.agreedAmount) if self.payment else 0,
            "job_title": self.payment.job.title
            if self.payment and self.payment.job
            else "Unknown",
            "created_date": self.dateCreated.strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": self.lastUpdated.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def processCallback(self, callbackData: dict):
        """
        Processes payment gateway callback data and updates status accordingly.

        :param callbackData: dict - Callback data from payment gateway
        :return: bool - True if callback was processed successfully
        """
        try:
            gateway_status = callbackData.get("status", "").upper()

            if gateway_status in ["COMPLETED", "SUCCESS", "SUCCESSFUL"]:
                self.markAsCompleted()

                # Update payment with gateway reference if available
                if self.payment and callbackData.get("reference"):
                    self.payment.mpesaReference = callbackData.get("reference")
                    self.payment.paymentMethod = callbackData.get(
                        "payment_method", "Gateway"
                    )

                return True

            elif gateway_status in ["FAILED", "CANCELLED", "DECLINED"]:
                self.markAsFailed()
                return True

            return False

        except Exception:
            # Log error and mark as failed
            self.markAsFailed()
            return False

    @classmethod
    def findByOrderTrackingId(cls, orderTrackingId: str):
        """
        Finds an interim payment record by order tracking ID.

        :param orderTrackingId: str - Order tracking ID from payment gateway
        :return: PaymentInterim|None - Found interim payment or None
        """
        return cls.query.filter_by(orderTrackingId=orderTrackingId).first()

    @classmethod
    def findByMerchantReference(cls, merchantReference: str):
        """
        Finds an interim payment record by merchant reference.

        :param merchantReference: str - Merchant reference for the payment
        :return: PaymentInterim|None - Found interim payment or None
        """
        return cls.query.filter_by(merchantReference=merchantReference).first()

    @classmethod
    def getProcessingPayments(cls):
        """
        Retrieves all payments currently being processed.

        :return: list - List of PaymentInterim objects in SAVED status
        """
        return cls.query.filter_by(status="SAVED").all()

    @classmethod
    def getCompletedPayments(cls):
        """
        Retrieves all successfully completed interim payments.

        :return: list - List of PaymentInterim objects in COMPLETED status
        """
        return cls.query.filter_by(status="COMPLETED").all()

    @classmethod
    def getFailedPayments(cls):
        """
        Retrieves all failed interim payments.

        :return: list - List of PaymentInterim objects in FAILED status
        """
        return cls.query.filter_by(status="FAILED").all()

    @classmethod
    def getStalePayments(cls, hoursOld: int = 24):
        """
        Retrieves interim payments that have been processing for too long.

        :param hoursOld: int - Hours after which a payment is considered stale
        :return: list - List of stale PaymentInterim objects
        """
        from datetime import datetime
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(hours=hoursOld)

        return cls.query.filter(
            cls.status == "SAVED", cls.dateCreated < cutoff_time
        ).all()

    @classmethod
    def cleanupStalePayments(cls, hoursOld: int = 48):
        """
        Marks stale payments as failed for cleanup.

        :param hoursOld: int - Hours after which to mark payments as failed
        :return: int - Number of payments marked as failed
        """
        stale_payments = cls.getStalePayments(hoursOld)
        count = 0

        for payment in stale_payments:
            payment.markAsFailed()
            count += 1

        return count

    @classmethod
    def getPaymentStatistics(cls):
        """
        Generates statistics for interim payments.

        :return: dict - Dictionary containing payment statistics
        """
        total_payments = cls.query.count()
        completed_payments = cls.query.filter_by(status="COMPLETED").count()
        failed_payments = cls.query.filter_by(status="FAILED").count()
        processing_payments = cls.query.filter_by(status="SAVED").count()

        success_rate = (
            (completed_payments / total_payments * 100)
            if total_payments > 0
            else 0
        )

        return {
            "total_payments": total_payments,
            "completed_payments": completed_payments,
            "failed_payments": failed_payments,
            "processing_payments": processing_payments,
            "success_rate": round(success_rate, 2),
            "failure_rate": round(
                (failed_payments / total_payments * 100)
                if total_payments > 0
                else 0,
                2,
            ),
        }
