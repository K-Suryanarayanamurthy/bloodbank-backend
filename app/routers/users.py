from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/all")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).filter(User.is_active == True, User.id != current_user.id).all()
    return [{"id": u.id, "full_name": u.full_name, "blood_group": u.blood_group, "city": u.city} for u in users]

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "full_name": user.full_name,
        "blood_group": user.blood_group,
        "city": user.city,
        "state": user.state,
        "phone": user.phone,
        "bio": user.bio,
        "is_available_to_donate": user.is_available_to_donate,
        "is_health_eligible": user.is_health_eligible,
    }
