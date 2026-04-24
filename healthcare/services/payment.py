"""Payment processing service – Stripe integration and receipt PDF generation."""

import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import Optional

logger = logging.getLogger(__name__)


def process_payment(db, bill, amount: float, method, stripe_payment_method_id: Optional[str] = None):
    """
    Process a payment for a bill.
    For card payments, uses Stripe. For others, records directly.
    Returns the Payment record.
    """
    from healthcare.models.billing import Payment, PaymentMethod, PaymentStatus, BillStatus

    payment = Payment(
        bill_id=bill.id,
        patient_id=bill.patient_id,
        amount=amount,
        method=method,
        status=PaymentStatus.pending,
    )
    db.add(payment)
    db.flush()

    if method in (PaymentMethod.credit_card, PaymentMethod.debit_card,
                  PaymentMethod.hsa, PaymentMethod.fsa) and stripe_payment_method_id:
        _process_stripe(db, payment, bill, amount, stripe_payment_method_id)
    else:
        # Non-card payments (cash, bank transfer) – mark as succeeded immediately
        payment.status = PaymentStatus.succeeded
        payment.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    _apply_payment_to_bill(db, bill, payment)
    db.add(payment)
    db.add(bill)
    return payment


def _process_stripe(db, payment, bill, amount: float, payment_method_id: str):
    """Create and confirm a Stripe PaymentIntent."""
    from healthcare.config import healthcare_settings
    from healthcare.models.billing import PaymentStatus

    secret_key = healthcare_settings.stripe_secret_key
    if not secret_key or secret_key == "your_stripe_secret_key_here":
        logger.warning("Stripe not configured – marking payment as succeeded (demo mode)")
        payment.status = PaymentStatus.succeeded
        payment.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        return

    try:
        import stripe
        stripe.api_key = secret_key
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses cents
            currency="usd",
            payment_method=payment_method_id,
            confirm=True,
            metadata={"bill_id": str(bill.id), "payment_id": str(payment.id)},
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )
        payment.stripe_payment_intent_id = intent.id
        if intent.status == "succeeded":
            payment.status = PaymentStatus.succeeded
            payment.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if intent.latest_charge:
                charge = stripe.Charge.retrieve(intent.latest_charge)
                payment.stripe_charge_id = charge.id
                payment.receipt_url = charge.receipt_url
        else:
            payment.status = PaymentStatus.processing
    except Exception as e:
        logger.error("Stripe payment error: %s", e)
        payment.status = PaymentStatus.failed
        raise


def _apply_payment_to_bill(db, bill, payment):
    """Update bill balance after a successful payment."""
    from healthcare.models.billing import PaymentStatus, BillStatus

    if payment.status == PaymentStatus.succeeded:
        bill.amount_paid = (bill.amount_paid or 0) + payment.amount
        bill.balance_due = max(0.0, bill.balance_due - payment.amount)
        if bill.balance_due <= 0.01:
            bill.status = BillStatus.paid
        elif bill.amount_paid > 0:
            bill.status = BillStatus.partially_paid


def handle_stripe_webhook(payload: bytes, sig_header: str, db):
    """Process incoming Stripe webhook events."""
    from healthcare.config import healthcare_settings
    from healthcare.models.billing import Payment, PaymentStatus, BillStatus

    secret = healthcare_settings.stripe_webhook_secret
    if not secret or secret == "your_stripe_webhook_secret_here":
        logger.warning("Stripe webhook secret not configured")
        return

    try:
        import stripe
        stripe.api_key = healthcare_settings.stripe_secret_key
        event = stripe.Webhook.construct_event(payload, sig_header, secret)
    except Exception as e:
        raise ValueError(f"Webhook verification failed: {e}")

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == intent["id"]
        ).first()
        if payment:
            payment.status = PaymentStatus.succeeded
            payment.processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            bill = payment.bill
            if bill:
                _apply_payment_to_bill(db, bill, payment)
            db.add(payment)

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == intent["id"]
        ).first()
        if payment:
            payment.status = PaymentStatus.failed
            db.add(payment)


def generate_receipt_pdf(bill, db) -> bytes:
    """Generate a PDF receipt for a bill using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("HEALTHCARE PLATFORM", styles["Title"]))
        elements.append(Paragraph("Medical Bill Receipt", styles["Heading2"]))
        elements.append(Spacer(1, 12))

        # Bill info
        elements.append(Paragraph(f"Bill #: {bill.id}", styles["Normal"]))
        if bill.statement_date:
            elements.append(Paragraph(f"Date: {bill.statement_date.strftime('%B %d, %Y')}", styles["Normal"]))
        elements.append(Spacer(1, 12))

        # Line items table
        data = [["Description", "Code", "Amount"]]
        for item in (bill.line_items or []):
            data.append([
                item.get("description", ""),
                item.get("code", ""),
                f"${item.get('amount', 0):.2f}",
            ])

        data.append(["", "Subtotal", f"${bill.subtotal:.2f}"])
        if bill.insurance_adjustment:
            data.append(["", "Insurance Adjustment", f"-${bill.insurance_adjustment:.2f}"])
        if bill.discount:
            data.append(["", "Discount", f"-${bill.discount:.2f}"])
        if bill.tax:
            data.append(["", "Tax", f"${bill.tax:.2f}"])
        data.append(["", "TOTAL DUE", f"${bill.total:.2f}"])
        data.append(["", "Amount Paid", f"${bill.amount_paid:.2f}"])
        data.append(["", "BALANCE DUE", f"${bill.balance_due:.2f}"])

        table = Table(data, colWidths=[250, 120, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, -3), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Thank you for choosing our healthcare services.", styles["Normal"]))

        doc.build(elements)
        return buffer.getvalue()
    except ImportError:
        # ReportLab not installed – return minimal text PDF placeholder
        logger.warning("ReportLab not installed, returning plain text receipt")
        text = f"Receipt - Bill #{bill.id}\nTotal: ${bill.total:.2f}\nBalance Due: ${bill.balance_due:.2f}"
        return text.encode()
