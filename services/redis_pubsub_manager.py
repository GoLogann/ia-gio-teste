import redis.asyncio as aioredis
from resources.redis.config import HOST, PORT

class RedisPubSubManager:
    def __init__(self, host=HOST, port=PORT):
        self.redis_host = host
        self.redis_port = port
        self.pubsub = None

    async def _get_redis_connection(self) -> aioredis.Redis:
        """
        Establishes a connection to Redis.

        Returns:
            aioredis.Redis: Redis connection object.
        """
        return aioredis.Redis(host=self.redis_host,
                              port=self.redis_port,
                              auto_close_connection_pool=False)

    async def connect(self) -> None:
        """
        Connects to the Redis server and initializes the pubsub client.
        """
        redis_connection = await self._get_redis_connection()
        self.pubsub = redis_connection.pubsub()

    async def publish(self, dialogue_id: str, message: str) -> None:
        """
        Publishes a message to a specific Redis channel.

        Args:
            dialogue_id (str): Channel or dialogue ID.
            message (str): Message to be published.
        """
        redis_connection = await self._get_redis_connection()
        await redis_connection.publish(dialogue_id, message)

    async def subscribe(self, dialogue_id: str) -> aioredis.Redis:
        """
        Subscribes to a Redis channel.

        Args:
            dialogue_id (str): Channel or dialogue ID to subscribe to.

        Returns:
            aioredis.ChannelSubscribe: PubSub object for the subscribed channel.
        """
        await self.pubsub.subscribe(dialogue_id)
        return self.pubsub

    async def unsubscribe(self, dialogue_id: str) -> None:
        """
        Unsubscribes from a Redis channel.

        Args:
            dialogue_id (str): Channel or dialogue ID to unsubscribe from.
        """
        await self.pubsub.unsubscribe(dialogue_id)