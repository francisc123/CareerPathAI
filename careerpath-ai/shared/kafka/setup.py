from setuptools import setup, find_packages

setup(
    name='cp-shared-kafka',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        "aiokafka>=0.8.1",
        "pydantic>=2.0.0",
    ],
    description="Shared Kafka async consumers and producers for CareerPathAI",
)