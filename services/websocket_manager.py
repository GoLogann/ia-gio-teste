import asyncio
import json

from starlette import status

from database.database import get_db
from repository.dialogo_repository import DialogoRepository
from services.redis_pubsub_manager import RedisPubSubManager
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.dialogues: dict = {}
        self.pubsub_client = RedisPubSubManager()

    async def add_user_to_dialogue(self, dialogue_id: str,  user_id: str, websocket: WebSocket) -> None:
        """
        Adds a user's WebSocket connection to a dialogue after validating access.

        Args:
            dialogue_id (str): Dialogue ID or channel name.
            websocket (WebSocket): WebSocket connection object.
            user_id (int): ID of the user trying to join the dialogue.
        """
        if not self._validate_user_access(
                dialogue_id=dialogue_id,
                user_id=user_id
        ):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()

        history = await self._get_message_history(dialogue_id=dialogue_id)
        for message in history:
            await websocket.send_text(data=json.dumps(message))

        if dialogue_id in self.dialogues:
            self.dialogues[dialogue_id].append(websocket)
        else:
            self.dialogues[dialogue_id] = [websocket]

            await self.pubsub_client.connect()
            pubsub_subscriber = await self.pubsub_client.subscribe(dialogue_id=dialogue_id)
            asyncio.create_task(self._pubsub_data_reader(pubsub_subscriber=pubsub_subscriber))

    async def broadcast_to_dialogue(self, dialogue_id: str, message: str) -> None:
        """
        Broadcasts a message to all connected WebSockets in a dialogue.

        Args:
            dialogue_id (str): Dialogue ID or channel name.
            message (str): Message to be broadcasted.
        """
        await self.pubsub_client.publish(
            dialogue_id=dialogue_id,
            message=message
        )

    async def remove_user_from_dialogue(self, dialogue_id: str, websocket: WebSocket) -> None:
        """
        Removes a user's WebSocket connection from a dialogue.

        Args:
            dialogue_id (str): Dialogue ID or channel name.
            websocket (WebSocket): WebSocket connection object.
        """
        self.dialogues[dialogue_id].remove(websocket)

        if len(self.dialogues[dialogue_id]) == 0:
            del self.dialogues[dialogue_id]
            await self.pubsub_client.unsubscribe(dialogue_id)

    async def _pubsub_data_reader(self, pubsub_subscriber):
        """
        Reads and broadcasts messages received from Redis PubSub.

        Args:
            pubsub_subscriber (aioredis.ChannelSubscribe): PubSub object for the subscribed channel.
        """
        while True:
            message = await pubsub_subscriber.get_message(ignore_subscribe_messages=True)
            if message is not None:
                dialogue_id = message['channel'].decode('utf-8')
                all_sockets = self.dialogues[dialogue_id]
                for socket in all_sockets:
                    data = message['data'].decode('utf-8')
                    await socket.send_text(data)

    @staticmethod
    async def _get_message_history(dialogue_id: str):
        """
        Retrieves the message history for a dialogue from PostgreSQL.

        Args:
            dialogue_id (str): Dialogue ID or channel name.

        Returns:
            list: List of historical messages.
        """
        db = get_db()
        dialogo_respository = DialogoRepository(db)
        return await dialogo_respository.fetch_message_history_from_db(dialogue_id)

    @staticmethod
    def _validate_user_access(dialogue_id: str, user_id: str) -> bool:
        """
        Validates if the user has access to the room.

        Args:
            dialogue_id (str): Room ID or channel name.
            user_id (int): ID of the user trying to join the room.

        Returns:
            bool: True if the user has access, False otherwise.
        """
        pass

