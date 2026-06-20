from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, BloodGroup
from app.models.health import HealthDeclaration
from app.models.donation import DonationRecord, DonationStatus

router = APIRouter()

# Health eligibility check logic
CRITICAL_CONDITIONS = [
    "has_hiv", "has_hepatitis", "has_cancer", "has_heart_disease",
    "has_tuberculosis", "is_pregnant"
]
TEMP_CONDITIONS = [
    "has_diabetes", "had_recent_surgery", "on_medication",
    "had_recent_tattoo", "had_fever_recently", "had_alcohol_recently"
]
CONDITION_LABELS = {
    "has_hiv": "HIV positive",
    "has_hepatitis": "Hepatitis",
    "has_cancer": "Cancer",
    "has_heart_disease": "Heart disease",
    "has_tuberculosis": "Tuberculosis",
    "is_pregnant": "Pregnant",
    "has_diabetes": "Diabetes",
    "had_recent_surgery": "Recent surgery (within 6 months)",
    "on_medication": "Currently on medication",
    "had_recent_tattoo": "Recent tattoo (within 6 months)",
    "had_fever_recently": "Fever in last 2 weeks",
    "had_alcohol_recently": "Alcohol in last 24 hours",
}

@router.post("/health-declaration")
def submit_health_declaration(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """User submits health declaration before donating. System auto-checks eligibility."""
    reasons = []

    for condition in CRITICAL_CONDITIONS + TEMP_CONDITIONS:
        if data.get(condition, False):
            reasons.append(CONDITION_LABELS.get(condition, condition))

    is_eligible = len(reasons) == 0
    ineligible_reason = ", ".join(reasons) if reasons else None

    declaration = HealthDeclaration(
        user_id=current_user.id,
        is_eligible=is_eligible,
        ineligible_reason=ineligible_reason,
        **{k: data.get(k, False) for k in CRITICAL_CONDITIONS + TEMP_CONDITIONS},
        other_conditions=data.get("other_conditions")
    )
    db.add(declaration)

    # Update user eligibility flag
    current_user.is_health_eligible = is_eligible
    db.commit()

    if is_eligible:
        return {"eligible": True, "message": "You are eligible to donate blood ✅"}
    else:
        return {
            "eligible": False,
            "message": "You are not eligible to donate at this time.",
            "reasons": reasons
        }

@router.get("/search")
def search_donors(
    blood_group: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for available and health-eligible donors by blood group and city."""
    query = db.query(User).filter(
        User.is_available_to_donate == True,
        User.is_health_eligible == True,
        User.is_active == True,
        User.id != current_user.id   # Exclude self
    )
    if blood_group:
        query = query.filter(User.blood_group == blood_group)
    if city:
        query = query.filter(User.city.ilike(f"%{city}%"))

    donors = query.all()
    return [
        {
            "id": d.id,
            "full_name": d.full_name,
            "blood_group": d.blood_group,
            "city": d.city,
            "state": d.state,
            "phone": d.phone,
            "bio": d.bio,
        }
        for d in donors
    ]

@router.post("/request-donation")
def request_donation(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seeker sends a donation request to a donor."""
    donor = db.query(User).filter(User.id == data.get("donor_id")).first()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")
    if not donor.is_health_eligible or not donor.is_available_to_donate:
        raise HTTPException(status_code=400, detail="Donor is not available")

    record = DonationRecord(
        donor_id=donor.id,
        seeker_id=current_user.id,
        blood_group=data.get("blood_group"),
        hospital_name=data.get("hospital_name"),
        city=data.get("city"),
        urgency_note=data.get("urgency_note"),
    )
    db.add(record)
    db.commit()
    return {"message": "Donation request sent successfully", "record_id": record.id}

@router.get("/my-donations")
def my_donation_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns donation history where user was the donor."""
    records = db.query(DonationRecord).filter(DonationRecord.donor_id == current_user.id).all()
    return [
        {
            "id": r.id,
            "seeker_name": r.seeker.full_name,
            "blood_group": r.blood_group,
            "hospital": r.hospital_name,
            "city": r.city,
            "status": r.status,
            "requested_at": r.requested_at,
        }
        for r in records
    ]

@router.get("/my-requests")
def my_request_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns blood requests made by this user."""
    records = db.query(DonationRecord).filter(DonationRecord.seeker_id == current_user.id).all()
    return [
        {
            "id": r.id,
            "donor_name": r.donor.full_name,
            "donor_phone": r.donor.phone,
            "blood_group": r.blood_group,
            "hospital": r.hospital_name,
            "status": r.status,
            "requested_at": r.requested_at,
        }
        for r in records
    ]

@router.put("/request/{record_id}/status")
def update_request_status(
    record_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Donor accepts, completes or cancels a donation request."""
    record = db.query(DonationRecord).filter(DonationRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.donor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    record.status = data.get("status")
    db.commit()
    return {"message": f"Status updated to {record.status}"}
