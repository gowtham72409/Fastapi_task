class RoomManager:

    def __init__(self):
        self.rooms = {}

    def join_room(self, room, username):

        if room not in self.rooms:
            self.rooms[room] = set()

        self.rooms[room].add(username)

    def leave_room(self, room, username):

        if room in self.rooms:
            self.rooms[room].discard(username)

    def get_users(self, room):

        return self.rooms.get(room, set())