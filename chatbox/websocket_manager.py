from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    # Added sender_id as an argument
    async def send_private_message(self, sender_id: int, receiver_id: int, message: str):
        receiver_ws = self.active_connections.get(receiver_id)
        if receiver_ws:
            # Send a JSON string containing both the sender and the content
            import json
            payload = json.dumps({"sender": sender_id, "message": message})
            await receiver_ws.send_text(payload)
        else:
            print(f"User {receiver_id} is not online")

manager = ConnectionManager()