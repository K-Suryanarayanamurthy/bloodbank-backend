from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user
)
from app.models.user import User
from app.models.otp import OTP
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    SendOTPRequest, VerifyOTPRequest, ResetPasswordRequest, ChangePasswordRequest
)
import random, string

router = APIRouter()

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

@router.post("/register", status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        city=data.city,
        state=data.state,
        blood_group=data.blood_group,
        is_health_eligible=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registration successful", "user_id": user.id}

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")
    return TokenResponse(
        access_token=create_access_token({"sub": str(user.id)}),
        refresh_token=create_refresh_token({"sub": str(user.id)})
    )

@router.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "city": current_user.city,
        "state": current_user.state,
        "blood_group": current_user.blood_group,
        "bio": current_user.bio,
        "is_available_to_donate": current_user.is_available_to_donate,
        "is_health_eligible": current_user.is_health_eligible,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at,
    }

@router.put("/profile/update")
def update_profile(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    allowed = ["full_name", "phone", "city", "state", "blood_group", "bio", "is_available_to_donate"]
    for key, value in data.items():
        if key in allowed:
            setattr(current_user, key, value)
    db.commit()
    return {"message": "Profile updated successfully"}

@router.post("/send-otp")
def send_otp(data: SendOTPRequest, db: Session = Depends(get_db)):
    from app.core.email import send_otp_email
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    otp_code = generate_otp()
    otp = OTP(user_id=user.id, otp_code=otp_code)
    db.add(otp)
    db.commit()
    sent = send_otp_email(user.email, user.full_name, otp_code)
    if sent:
        return {"message": "OTP sent to your email"}
    else:
        return {"message": "OTP generated", "dev_otp": otp_code}

@router.post("/verify-otp")
def verify_otp(data: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    otp = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.otp_code == data.otp_code,
        OTP.is_used == False
    ).order_by(OTP.created_at.desc()).first()
    if not otp or otp.is_expired():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"message": "OTP verified successfully"}

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    otp = db.query(OTP).filter(
        OTP.user_id == user.id,
        OTP.otp_code == data.otp_code,
        OTP.is_used == False
    ).order_by(OTP.created_at.desc()).first()
    if not otp or otp.is_expired():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    user.password_hash = hash_password(data.new_password)
    otp.is_used = True
    db.commit()
    return {"message": "Password reset successfully"}

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.delete("/delete")
def delete_account(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}
