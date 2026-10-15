from app import db


class Payment(db.Model):
    """
    Model representing a Payment agreement for completed jobs.
    Tracks payment status and integrates with payment gateways.
    """

    __tablename__ = "payment"

    paymentId = db.Column(db.Integer, autoincrement=True, primary_key=True)
    jobId = db.Column(db.Integer, db.ForeignKey("job.jobId"), nullable=False)
    agreedAmount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.Enum("agreed", "paid", "completed"), default="agreed", nullable=False
    )
    paymentMethod = db.Column(db.String(50), nullable=True)
    mpesaReference = db.Column(db.String(100), nullable=True)
    invoiceNumber = db.Column(db.String(50), nullable=True)
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
    job = db.relationship("Job", back_populates="payment")
    paymentInterim = db.relationship(
        "PaymentInterim",
        back_populates="payment",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """
        String representation of the Payment object.

        :return: str - String representation showing paymentId, amount and status
        """
        return f"Payment(paymentId={self.paymentId}, jobId={self.jobId}, amount=${self.agreedAmount}, status={self.status})"

    def generateInvoiceNumber(self):
        """
        Generates a unique invoice number for this payment.

        :return: str - Generated invoice number
        """
        import uuid
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        self.invoiceNumber = f"INV-{timestamp}-{unique_id}"
        db.session.commit()
        return self.invoiceNumber

    def updatePaymentStatus(
        self, newStatus: str, paymentMethod: str = None, reference: str = None
    ):
        """
        Updates the payment status and related information.

        :param newStatus: str - New payment status ('agreed', 'paid', 'completed')
        :param paymentMethod: str - Payment method used
        :param reference: str - Payment reference (e.g., M-Pesa reference)
        :return: bool - True if update was successful, False otherwise
        """
        valid_statuses = ["agreed", "paid", "completed"]
        if newStatus not in valid_statuses:
            return False

        self.status = newStatus

        if paymentMethod:
            self.paymentMethod = paymentMethod

        if reference:
            if paymentMethod and paymentMethod.lower() == "mpesa":
                self.mpesaReference = reference

        db.session.commit()
        return True

    def markAsPaid(self, paymentMethod: str, reference: str = None):
        """
        Marks the payment as paid with payment details.

        :param paymentMethod: str - Method used for payment
        :param reference: str - Payment reference number
        :return: None
        """
        self.status = "paid"
        self.paymentMethod = paymentMethod

        if reference:
            if paymentMethod.lower() == "mpesa":
                self.mpesaReference = reference

        db.session.commit()

    def markAsCompleted(self):
        """
        Marks the payment as completed (final step in payment process).

        :return: bool - True if payment was marked completed, False otherwise
        """
        if self.status == "paid":
            self.status = "completed"
            db.session.commit()
            return True
        return False

    def initiatePaymentProcess(self):
        """
        Initiates the payment process by creating interim payment record.

        :return: PaymentInterim - The created interim payment record
        """
        from .payment_interim import PaymentInterim
        import uuid

        # Generate unique tracking references
        orderTrackingId = f"ORDER-{uuid.uuid4()}"
        merchantReference = f"PAY-{self.paymentId}-{uuid.uuid4().hex[:8]}"

        interim = PaymentInterim(
            paymentId=self.paymentId,
            orderTrackingId=orderTrackingId,
            merchantReference=merchantReference,
            iframeSrc="",  # Will be updated when payment gateway responds
            status="SAVED",
        )

        db.session.add(interim)
        db.session.commit()
        return interim

    def getPaymentDetails(self):
        """
        Returns comprehensive payment details for display.

        :return: dict - Dictionary containing payment information
        """
        return {
            "payment_id": self.paymentId,
            "job_id": self.jobId,
            "job_title": self.job.title if self.job else "Unknown",
            "amount": float(self.agreedAmount),
            "status": self.status.title(),
            "payment_method": self.paymentMethod or "Not specified",
            "mpesa_reference": self.mpesaReference,
            "invoice_number": self.invoiceNumber,
            "created_date": self.dateCreated.strftime("%Y-%m-%d %H:%M"),
            "last_updated": self.lastUpdated.strftime("%Y-%m-%d %H:%M"),
        }

    def isPending(self):
        """
        Checks if payment is still pending (agreed status).

        :return: bool - True if payment is pending, False otherwise
        """
        return self.status == "agreed"

    def isProcessing(self):
        """
        Checks if payment is currently being processed.

        :return: bool - True if payment is being processed, False otherwise
        """
        return self.paymentInterim and self.paymentInterim.status == "SAVED"

    def isCompleted(self):
        """
        Checks if payment process is fully completed.

        :return: bool - True if payment is completed, False otherwise
        """
        return self.status == "completed"

    @classmethod
    def createPaymentAgreement(cls, jobId: int, agreedAmount: float):
        """
        Creates a new payment agreement for a job.

        :param jobId: int - ID of the job
        :param agreedAmount: float - Amount agreed upon for payment
        :return: Payment - The newly created Payment object
        """
        payment = cls(jobId=jobId, agreedAmount=agreedAmount, status="agreed")

        db.session.add(payment)
        db.session.commit()

        # Generate invoice number
        payment.generateInvoiceNumber()

        return payment

    @classmethod
    def getPendingPayments(cls):
        """
        Retrieves all payments that are still pending.

        :return: list - List of pending Payment objects
        """
        return cls.query.filter_by(status="agreed").all()

    @classmethod
    def getCompletedPayments(cls):
        """
        Retrieves all completed payments.

        :return: list - List of completed Payment objects
        """
        return cls.query.filter_by(status="completed").all()

    @classmethod
    def getPaymentsByMethod(cls, paymentMethod: str):
        """
        Retrieves payments made using a specific payment method.

        :param paymentMethod: str - Payment method to filter by
        :return: list - List of Payment objects using the specified method
        """
        return cls.query.filter_by(paymentMethod=paymentMethod).all()

    @classmethod
    def getPaymentsInRange(cls, minAmount: float, maxAmount: float):
        """
        Retrieves payments within a specific amount range.

        :param minAmount: float - Minimum payment amount
        :param maxAmount: float - Maximum payment amount
        :return: list - List of Payment objects within the range
        """
        return cls.query.filter(
            cls.agreedAmount >= minAmount, cls.agreedAmount <= maxAmount
        ).all()

    @classmethod
    def getTotalPaymentsValue(cls):
        """
        Calculates the total value of all completed payments.

        :return: float - Total value of completed payments
        """
        result = (
            db.session.query(db.func.sum(cls.agreedAmount))
            .filter_by(status="completed")
            .scalar()
        )
        return float(result) if result else 0.0

    @classmethod
    def getMonthlyPaymentsReport(cls, year: int, month: int):
        """
        Generates a monthly payments report.

        :param year: int - Year for the report
        :param month: int - Month for the report
        :return: dict - Dictionary containing monthly payment statistics
        """
        from sqlalchemy import extract

        monthly_payments = cls.query.filter(
            extract("year", cls.dateCreated) == year,
            extract("month", cls.dateCreated) == month,
        ).all()

        total_amount = sum(payment.agreedAmount for payment in monthly_payments)
        completed_payments = [
            p for p in monthly_payments if p.status == "completed"
        ]
        completed_amount = sum(
            payment.agreedAmount for payment in completed_payments
        )

        return {
            "year": year,
            "month": month,
            "total_payments": len(monthly_payments),
            "completed_payments": len(completed_payments),
            "total_amount": float(total_amount),
            "completed_amount": float(completed_amount),
            "completion_rate": (
                len(completed_payments) / len(monthly_payments) * 100
            )
            if monthly_payments
            else 0,
        }
