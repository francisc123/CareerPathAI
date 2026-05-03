import json
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

class KafkaProducerBase:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = AIOKafkaProducer(bootstrap_servers=self.bootstrap_servers)

    async def start(self):
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_message(self, topic:str, message: BaseModel):

        payload = message.model_dump_json().encode("utf-8")
        await self.producer.send_and_wait(topic, payload)

