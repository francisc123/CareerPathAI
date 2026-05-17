"""
Spawns the three completion-stage consumers as background asyncio tasks and
keeps a handle so the lifespan teardown can cancel them cleanly.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from . import (
    interview_hr_completed_consumer,
    interview_tech_completed_consumer,
    learning_completed_consumer,
)
from . import profile_db, workflow_completed_publisher

logger = logging.getLogger(__name__)

_tasks: list[asyncio.Task] = []


async def start_completion_consumers() -> None:
    await profile_db.init_pool()
    await workflow_completed_publisher.init_producer()

    loop = asyncio.get_running_loop()
    coros: Iterable = (
        learning_completed_consumer.consume(),
        interview_hr_completed_consumer.consume(),
        interview_tech_completed_consumer.consume(),
    )
    for coro in coros:
        _tasks.append(loop.create_task(coro))
    logger.info("Started %d completion consumers.", len(_tasks))


async def stop_completion_consumers() -> None:
    for task in _tasks:
        task.cancel()
    for task in _tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Consumer task raised on shutdown.")
    _tasks.clear()

    await workflow_completed_publisher.stop_producer()
    await profile_db.close_pool()
