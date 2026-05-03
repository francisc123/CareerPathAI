import asyncio
import json
import logging
from abc import ABC, abstractmethod
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logger = logging.getLogger(__name__)

class KafkaConsumerBase(ABC):
    def __init__(self, topic: str, bootstrap_servers: str, group_id: str, dlq_topic: str = None):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.dlq_topic = dlq_topic
        self._running = False

        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=False
        )
        self.dlq_producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers) if dlq_topic else None

    @abstractmethod
    async def handle_message(self, event: dict):
        """Trebuie implementată de fiecare serviciu."""
        pass

    async def start(self):
        await self.consumer.start()
        if self.dlq_producer:
            await self.dlq_producer.start()
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())

    async def stop(self):
        self._running = False
        if hasattr(self, '_task'):
            self._task.cancel()
        await self.consumer.stop()
        if self.dlq_producer:
            await self.dlq_producer.stop()

    async def _consume_loop(self):
        try:
            async for msg in self.consumer:
                if not self._running:
                    break

                try:
                    event = json.loads(msg.value.decode("utf-8"))
                    success = await self._process_with_retries(event)
                except json.JSONDecodeError:
                    logger.error("Eroare la decodarea JSON-ului.")
                    success = False

                if success:
                    await self.consumer.commit()
                else:
                    await self._send_to_dlq(msg.value)
                    await self.consumer.commit()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Eroare critică în consumer: {e}")

    async def _process_with_retries(self, event: dict) -> bool:
        max_retries = 3
        base_delay = 1

        for attempt in range(max_retries):
            try:
                await self.handle_message(event)
                return True
            except Exception as e:
                logger.error(f"Încercarea {attempt + 1} a eșuat: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) # Exponential backoff: 1, 2, 4 secunde
                    await asyncio.sleep(delay)
        return False

    async def _send_to_dlq(self, raw_value: bytes):
        if self.dlq_producer and self.dlq_topic:
            await self.dlq_producer.send_and_wait(self.dlq_topic, raw_value)
            logger.warning(f"Mesaj trimis în DLQ: {self.dlq_topic}")
        else:
            logger.error("Mesaj pierdut! Procesarea a eșuat și nu există DLQ configurat.")