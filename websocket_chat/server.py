import asyncio
import websockets
import json
from models import save_message
from manager import ConnectionManager
from room_manager import RoomManager

manager = ConnectionManager()
rooms = RoomManager()


async def chat(websocket):

    try:

        data = await websocket.recv()
        user_data = json.loads(data)

        username = user_data["username"]
        room = user_data["room"]

        await manager.connect(username, websocket)

        rooms.join_room(room, username)

        print(username, "joined", room)

        async for message in websocket:

            print("message:", message)

            users = rooms.get_users(room)

            save_message(username, room, message)

            for user in users:
                await manager.send(user, f"{username}: {message}")

    except Exception as e:
        print("Error:", e)

    finally:

        manager.disconnect(username)
        rooms.leave_room(room, username)

async def main():

    server = await websockets.serve(chat, "localhost", 8765)

    print("Chat server started")

    await server.wait_closed()


asyncio.run(main())

