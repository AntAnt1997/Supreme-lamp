"""Insurance eligibility and claims service."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def check_eligibility(patient_id: int, db) -> dict:
    """
    Check insurance eligibility for a patient.
    In production this would call a clearinghouse API (e.g. Change Healthcare, Availity).
    """
    from healthcare.models.patient import Patient

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {"eligible": False, "reason": "Patient not found"}

    if not patient.insurance_provider or not patient.insurance_member_id:
        return {"eligible": False, "reason": "No insurance on file"}

    # Demo: assume eligible if insurance info is present
    return {
        "eligible": True,
        "insurance_provider": patient.insurance_provider,
        "member_id": patient.insurance_member_id,
        "plan_name": patient.insurance_plan_name or "Unknown Plan",
        "group_number": patient.insurance_group_number,
        "deductible_remaining": 500.00,   # Placeholder
        "out_of_pocket_remaining": 1500.00,
        "copay": 25.00,
        "message": "Eligibility verified (demo mode)",
    }


def submit_claim(bill_id: int, db) -> dict:
    """
    Submit an insurance claim for a bill.
    In production this would use X12 EDI 837 format via a clearinghouse.
    """
    from healthcare.models.billing import Bill, ClaimStatus
    import secrets

    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        return {"success": False, "error": "Bill not found"}

    if bill.claim_status != ClaimStatus.not_submitted:
        return {"success": False, "error": f"Claim already in status: {bill.claim_status}"}

    # Generate a demo claim ID
    claim_id = f"CLM-{bill_id:06d}-{secrets.token_hex(4).upper()}"
    bill.claim_id = claim_id
    bill.claim_status = ClaimStatus.submitted
    db.add(bill)

    logger.info("Insurance claim %s submitted for bill %d (demo mode)", claim_id, bill_id)
    return {"success": True, "claim_id": claim_id, "status": ClaimStatus.submitted}


def get_claim_status(bill_id: int, db) -> dict:
    """Return the current insurance claim status for a bill."""
    from healthcare.models.billing import Bill

    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        return {"error": "Bill not found"}
    return {
        "bill_id": bill_id,
        "claim_id": bill.claim_id,
        "claim_status": bill.claim_status,
        "insurance_adjustment": bill.insurance_adjustment,
        "eob": bill.insurance_eob,
    }
