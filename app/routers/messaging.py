from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, List
import json

from app.database import get_db, SessionLocal
from app.models.message import Message
from app.models.user import User
from app.schemas.message import SendMessageRequest, MessageResponse, UnreadCountResponse
from app.core.security import get_current_user, decode_token

router = APIRouter(prefix="/api/messaging", tags=["Messaging"])


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        # user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict):
        ws = self.active_connections.get(user_id)
        if ws:
            await ws.send_text(json.dumps(message))


manager = ConnectionManager()


@router.websocket("/ws/{token}")
async def websocket_chat(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time chat.
    Connect: ws://host/api/messaging/ws/<jwt_token>
    Send: { "receiver_id": 5, "content": "Hello!" }
    Receive: { "sender_id": 3, "content": "Hello!", "created_at": "..." }
    """
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=4001)
        return

    await manager.connect(user_id, websocket)

    db: Session = SessionLocal()
    try:
        while True:
            data = await websocket.receive_text()
            msg_data = json.loads(data)

            receiver_id = msg_data.get("receiver_id")
            content = msg_data.get("content", "").strip()

            if not receiver_id or not content:
                continue

            receiver = db.query(User).filter(User.id == receiver_id, User.is_active == True).first()
            if not receiver:
                continue

            # Save to DB
            message = Message(
                sender_id=user_id,
                receiver_id=receiver_id,
                content=content
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            msg_payload = {
                "id": message.id,
                "sender_id": user_id,
                "receiver_id": receiver_id,
                "content": content,
                "is_read": False,
                "created_at": message.created_at.isoformat()
            }

            # Deliver to receiver if online
            await manager.send_to_user(receiver_id, msg_payload)
            # Echo back to sender
            await manager.send_to_user(user_id, msg_payload)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    finally:
        db.close()


@router.post("/send", response_model=MessageResponse)
def send_message_http(
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """HTTP fallback for sending messages (WebSocket is preferred)"""
    if payload.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    receiver = db.query(User).filter(User.id == payload.receiver_id, User.is_active == True).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")

    message = Message(
        sender_id=current_user.id,
        receiver_id=payload.receiver_id,
        content=payload.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/conversation/{other_user_id}", response_model=List[MessageResponse])
def get_conversation(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full conversation between current user and another user. Marks as read."""
    messages = db.query(Message).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    # Mark incoming as read
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.is_read:
            msg.is_read = True
    db.commit()
    return messages


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Message).filter(
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).count()
    return {"unread_count": count}


@router.post("/mark-read/{other_user_id}")
def mark_read(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(Message).filter(
        Message.sender_id == other_user_id,
        Message.receiver_id == current_user.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Messages marked as read"}
