from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user, decode_token
from app.models.user import User
from app.models.message import Message

router = APIRouter()

# ── WebSocket Connection Manager ──────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.active: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.active[user_id] = ws

    def disconnect(self, user_id: int):
        self.active.pop(user_id, None)

    async def send_to(self, user_id: int, data: dict):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_json(data)

manager = ConnectionManager()

# ── WebSocket endpoint ─────────────────────────────────────────────────────────
@router.websocket("/ws/{token}")
async def websocket_chat(token: str, websocket: WebSocket):
    """
    Real-time WebSocket chat.
    Connect: ws://host/api/chat/ws/<jwt_access_token>
    Send:    {"receiver_id": 5, "content": "Hello!"}
    Receive: {"from_user_id": 3, "from_name": "Surya", "content": "Hello!", "sent_at": "..."}
    """
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001)
        return

    user_id = int(payload.get("sub"))
    db: Session = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=4001)
            return

        await manager.connect(user_id, websocket)

        while True:
            data = await websocket.receive_json()
            receiver_id = data.get("receiver_id")
            content = data.get("content", "").strip()

            if not receiver_id or not content:
                continue

            # Save to DB
            msg = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
            db.add(msg)
            db.commit()
            db.refresh(msg)

            payload_out = {
                "from_user_id": user_id,
                "from_name": user.full_name,
                "content": content,
                "sent_at": str(msg.sent_at),
                "message_id": msg.id,
            }

            # Deliver to receiver if online
            await manager.send_to(receiver_id, payload_out)
            # Echo back to sender
            await manager.send_to(user_id, payload_out)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    finally:
        db.close()

# ── REST endpoints for chat history ───────────────────────────────────────────
@router.get("/conversation/{other_user_id}")
def get_conversation(
    other_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.sent_at.asc()).all()

    # Mark received messages as read
    for m in messages:
        if m.receiver_id == current_user.id and not m.is_read:
            m.is_read = True
    db.commit()

    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": m.sender.full_name,
            "content": m.content,
            "is_read": m.is_read,
            "sent_at": m.sent_at,
        }
        for m in messages
    ]

@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = db.query(Message).filter(
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).count()
    return {"unread_count": count}

@router.get("/contacts")
def get_contacts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns all users this person has chatted with."""
    from sqlalchemy import or_
    messages = db.query(Message).filter(
        or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
    ).all()

    contact_ids = set()
    for m in messages:
        contact_ids.add(m.sender_id if m.sender_id != current_user.id else m.receiver_id)

    contacts = db.query(User).filter(User.id.in_(contact_ids)).all()
    return [{"id": c.id, "full_name": c.full_name, "blood_group": c.blood_group} for c in contacts]
