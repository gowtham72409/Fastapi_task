class ConnectionManager:

    def __init__(self):
        self.active_users = {}

    async def connect(self, username, websocket):
        self.active_users[username] = websocket
        print(f"{username} connected")

    def disconnect(self, username):
        if username in self.active_users:
            del self.active_users[username]
            print(f"{username} disconnected")

    async def send(self, username, message):

        websocket = self.active_users.get(username)

        if websocket:
            await websocket.send(message)