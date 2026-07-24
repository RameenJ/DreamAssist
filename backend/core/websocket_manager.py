from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # Maps user_id (str) to their active WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """A new user has connected."""
        self.active_connections[user_id] = websocket
        print(f"INFO: WebSocket connected for user: {user_id}")

    def disconnect(self, user_id: str):
        """A user has disconnected."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"INFO: WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: str, user_id: str):
        """Send a message to a specific user."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_text(message)
            
    async def broadcast_json(self, data: dict, user_id: str):
        """Send JSON data to a specific user."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(data)

# Create a single, global instance of the manager
manager = ConnectionManager()