from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import models, json
from database import get_db
from websocket_manager import manager

router = APIRouter(prefix="/chat", tags=["chat"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    # Accept connection based on the user_id provided by the frontend
    await manager.connect(user_id, websocket)
    
    db = next(get_db()) 
    # Inside your websocket_endpoint loop:
    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)

            receiver_id = int(data_json["receiver_id"])
            message_text = data_json["message"]

        # Save to Database
            db_message = models.Message(
                sender_id=user_id,
                receiver_id=receiver_id,
                content=message_text
            )
            db.add(db_message)
            db.commit()

        # FIXED: Passing 3 arguments: sender_id, receiver_id, and message_text
            await manager.send_private_message(
                user_id, 
                receiver_id, 
                message_text
            )

    except WebSocketDisconnect():
        return {"disconnected"}