"""Billing & payment API routes."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from healthcare.api.auth_utils import get_current_user, require_staff
from healthcare.database.db import get_db
from healthcare.models.billing import Bill, Payment, BillStatus, PaymentMethod, PaymentStatus, ClaimStatus
from healthcare.models.patient import Patient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class LineItem(BaseModel):
    description: str
    code: Optional[str] = None
    amount: float


class BillCreate(BaseModel):
    patient_id: int
    appointment_id: Optional[int] = None
    line_items: List[LineItem]
    insurance_adjustment: float = 0.0
    discount: float = 0.0
    tax: float = 0.0
    due_date: Optional[datetime] = None


class BillOut(BaseModel):
    id: int
    patient_id: int
    appointment_id: Optional[int]
    subtotal: float
    insurance_adjustment: float
    discount: float
    tax: float
    total: float
    amount_paid: float
    balance_due: float
    status: str
    claim_status: str
    due_date: Optional[datetime]
    is_payment_plan: bool
    payment_plan_monthly_amount: Optional[float]

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    bill_id: int
    amount: float
    method: PaymentMethod
    # For card payments – Stripe PaymentMethod ID created on the frontend
    stripe_payment_method_id: Optional[str] = None


class PaymentPlanRequest(BaseModel):
    bill_id: int
    months: int


# ── Bill Endpoints ─────────────────────────────────────────────────────────────

@router.post("/bills", response_model=BillOut, status_code=201)
def create_bill(body: BillCreate, _=Depends(require_staff), db: Session = Depends(get_db)):
    subtotal = sum(item.amount for item in body.line_items)
    total = max(0.0, subtotal - body.insurance_adjustment - body.discount + body.tax)
    bill = Bill(
        patient_id=body.patient_id,
        appointment_id=body.appointment_id,
        line_items=[item.model_dump() for item in body.line_items],
        subtotal=subtotal,
        insurance_adjustment=body.insurance_adjustment,
        discount=body.discount,
        tax=body.tax,
        total=total,
        balance_due=total,
        status=BillStatus.issued,
        due_date=body.due_date,
        statement_date=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(bill)
    db.flush()

    # Notify patient
    try:
        from healthcare.workers.billing_worker import notify_bill_issued
        notify_bill_issued.delay(bill.id)
    except Exception:
        pass

    return bill


@router.get("/bills", response_model=List[BillOut])
def list_bills(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, Patient):
        return db.query(Bill).filter(Bill.patient_id == current_user.id).order_by(Bill.created_at.desc()).all()
    # Staff sees all
    return db.query(Bill).order_by(Bill.created_at.desc()).limit(200).all()


@router.get("/bills/{bill_id}", response_model=BillOut)
def get_bill(bill_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(404, "Bill not found")
    if isinstance(current_user, Patient) and bill.patient_id != current_user.id:
        raise HTTPException(403, "Access denied")
    return bill


@router.get("/bills/{bill_id}/receipt")
def download_receipt(bill_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(404, "Bill not found")
    if isinstance(current_user, Patient) and bill.patient_id != current_user.id:
        raise HTTPException(403, "Access denied")

    from healthcare.services.payment import generate_receipt_pdf
    pdf_bytes = generate_receipt_pdf(bill, db)
    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=receipt-{bill_id}.pdf"},
    )


# ── Payment Endpoints ──────────────────────────────────────────────────────────

@router.post("/payments", status_code=201)
def make_payment(
    body: PaymentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.query(Bill).filter(Bill.id == body.bill_id).first()
    if not bill:
        raise HTTPException(404, "Bill not found")
    if isinstance(current_user, Patient) and bill.patient_id != current_user.id:
        raise HTTPException(403, "Access denied")
    if body.amount <= 0:
        raise HTTPException(400, "Payment amount must be positive")
    if body.amount > bill.balance_due + 0.01:
        raise HTTPException(400, f"Payment exceeds balance due ({bill.balance_due:.2f})")

    from healthcare.services.payment import process_payment
    payment = process_payment(db, bill, body.amount, body.method, body.stripe_payment_method_id)
    return {
        "payment_id": payment.id,
        "status": payment.status,
        "amount": payment.amount,
        "receipt_url": payment.receipt_url,
    }


@router.post("/payments/plan")
def setup_payment_plan(
    body: PaymentPlanRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = db.query(Bill).filter(Bill.id == body.bill_id).first()
    if not bill:
        raise HTTPException(404, "Bill not found")
    if isinstance(current_user, Patient) and bill.patient_id != current_user.id:
        raise HTTPException(403, "Access denied")
    if body.months < 1:
        raise HTTPException(400, "Months must be at least 1")

    monthly = round(bill.balance_due / body.months, 2)
    bill.is_payment_plan = True
    bill.payment_plan_months = body.months
    bill.payment_plan_monthly_amount = monthly
    db.add(bill)
    return {"monthly_payment": monthly, "months": body.months, "total": bill.balance_due}


@router.get("/payments")
def payment_history(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if isinstance(current_user, Patient):
        payments = (
            db.query(Payment)
            .filter(Payment.patient_id == current_user.id)
            .order_by(Payment.created_at.desc())
            .limit(50)
            .all()
        )
    else:
        payments = db.query(Payment).order_by(Payment.created_at.desc()).limit(200).all()
    return [
        {
            "id": p.id,
            "bill_id": p.bill_id,
            "amount": p.amount,
            "method": p.method,
            "status": p.status,
            "processed_at": p.processed_at,
            "receipt_url": p.receipt_url,
        }
        for p in payments
    ]


# ── Stripe Webhook ─────────────────────────────────────────────────────────────

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe events (payment_intent.succeeded, payment_intent.payment_failed)."""
    from healthcare.services.payment import handle_stripe_webhook
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        handle_stripe_webhook(payload, sig, db)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"received": True}
