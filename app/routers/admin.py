from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_admin_user
from app.models.user import User
from app.models.donation import DonationRecord
from app.models.health import HealthDeclaration

router = APIRouter()

@router.get("/users")
def admin_list_users(db: Session = Depends(get_db), admin=Depends(get_admin_user)):
    users = db.query(User).all()
    return [
        {
            "id": u.id, "full_name": u.full_name, "email": u.email,
            "blood_group": u.blood_group, "city": u.city,
            "is_health_eligible": u.is_health_eligible,
            "is_available_to_donate": u.is_available_to_donate,
            "is_active": u.is_active, "is_admin": u.is_admin,
            "created_at": u.created_at,
        }
        for u in users
    ]

@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, db: Session = Depends(get_db), admin=Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}"}

@router.delete("/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db), admin=Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}

@router.get("/donations")
def admin_all_donations(db: Session = Depends(get_db), admin=Depends(get_admin_user)):
    records = db.query(DonationRecord).all()
    return [
        {
            "id": r.id,
            "donor": r.donor.full_name,
            "seeker": r.seeker.full_name,
            "blood_group": r.blood_group,
            "status": r.status,
            "requested_at": r.requested_at,
        }
        for r in records
    ]

@router.get("/stats")
def admin_stats(db: Session = Depends(get_db), admin=Depends(get_admin_user)):
    total_users      = db.query(User).count()
    eligible_donors  = db.query(User).filter(User.is_health_eligible == True, User.is_available_to_donate == True).count()
    total_donations  = db.query(DonationRecord).count()
    completed        = db.query(DonationRecord).filter(DonationRecord.status == "completed").count()
    return {
        "total_users": total_users,
        "eligible_donors": eligible_donors,
        "total_donation_requests": total_donations,
        "completed_donations": completed,
    }
