import asyncio
from unittest.mock import Mock

import pytest
from telethon.events.common import EventBuilder

from tgtestkit.update_recorder import UpdateRecorder

MockEvent = Mock(EventBuilder)

@pytest.fixture
def rec():
    return UpdateRecorder()

async def test_record_event(rec):
    await rec.record_update(MockEvent())
    await rec.record_update(MockEvent())
    await rec.record_update(MockEvent())

    assert len(rec) == len(rec.updates) == 3


async def test_stop(rec):
    await rec.record_update(MockEvent())
    await rec.record_update(MockEvent())
    await rec.record_update(MockEvent())

    rec.stop()

    # All incoming updates must be ignored after `stop` was called.
    await rec.record_update(MockEvent())
    await rec.record_update(MockEvent())

    assert len(rec) == 3


async def test_wait_at_least_one(rec):
    # Under the hood the wait_at_least_one calls `_any_received` Event.
    assert not rec._any_received.is_set()
    await rec.record_update(MockEvent())

    assert rec._any_received.is_set()


async def test_wait_until(rec):
    task = asyncio.create_task(
        rec.wait_until(lambda updates: len(updates) > 4),
    )

    assert not task.done()

    for _ in range(5):
        await rec.record_update(MockEvent())

    await asyncio.wait_for(task, 1)

    assert task.done()
