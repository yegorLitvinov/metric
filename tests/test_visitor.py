from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock

import pytest
from asyncpg.exceptions import ForeignKeyViolationError

from app.visitor.models import increment_counter
from app.connections.db import get_db_pool

pytestmark = pytest.mark.asyncio


async def test_increment_error_no_user(db, event_loop):
    cookie = str(uuid4())
    with pytest.raises(ForeignKeyViolationError):
        await increment_counter(0, cookie, '/')


async def test_increment_error_wrong_uuid(db, user, event_loop):
    with pytest.raises(ValueError):
        await increment_counter(user.id, '', '/')


async def test_increment_success_increase(db, event_loop, user, admin):
    pool = await get_db_pool()
    cookie = uuid4()
    await increment_counter(user.id, cookie, '/')

    async with pool.acquire() as conn:
        visitors = await conn.fetch('select * from visitor')
    assert len(visitors) == 1
    visitor = visitors[0]
    assert visitor['cookie'] == cookie
    assert visitor['account_id'] == user.id
    assert visitor['date'] == datetime.now().date()
    assert visitor['path'] == '/'
    assert visitor['hits'] == 1

    await increment_counter(user.id, cookie, '/')
    async with pool.acquire() as conn:
        visitors = await conn.fetch('select * from visitor')
    assert len(visitors) == 1
    visitor2 = visitors[0]
    assert visitor2['id'] == visitor['id']
    assert visitor2['hits'] == 2


async def test_increment_success_another_path(db, event_loop, user, admin):
    pool = await get_db_pool()
    cookie = uuid4()
    await increment_counter(user.id, cookie, '/')
    await increment_counter(user.id, cookie, '/about/')

    async with pool.acquire() as conn:
        visitors = await conn.fetch('select * from visitor')
    assert len(visitors) == 2
    visitor2 = visitors[1]
    assert visitor2['cookie'] == cookie
    assert visitor2['hits'] == 1


async def test_increment_success_another_visitor(db, event_loop, user, admin):
    pool = await get_db_pool()
    cookie = uuid4()
    await increment_counter(user.id, cookie, '/')
    cookie = uuid4()
    await increment_counter(user.id, cookie, '/')

    async with pool.acquire() as conn:
        visitors = await conn.fetch('select * from visitor')
    assert len(visitors) == 2
    visitor2 = visitors[1]
    assert visitor2['cookie'] == cookie
    assert visitor2['hits'] == 1


async def test_increment_success_another_account(db, event_loop, user, admin):
    pool = await get_db_pool()
    cookie = uuid4()
    await increment_counter(user.id, cookie, '/')
    await increment_counter(admin.id, cookie, '/')

    async with pool.acquire() as conn:
        visitors = await conn.fetch('select * from visitor')
    assert len(visitors) == 2
    visitor2 = visitors[1]
    assert visitor2['cookie'] == cookie
    assert visitor2['hits'] == 1


async def test_increment_success_tomorrow(db, event_loop, user, monkeypatch):
    pool = await get_db_pool()
    cookie = uuid4()
    await increment_counter(user.id, cookie, '/')

    tomorrow = datetime.now() + timedelta(days=1)
    datetime_mock = MagicMock()
    datetime_mock.now.return_value = tomorrow
    import app.visitor.models
    monkeypatch.setattr(app.visitor.models, 'datetime', datetime_mock)

    await increment_counter(user.id, cookie, '/')
    async with pool.acquire() as conn:
        visitors = await conn.fetch('select * from visitor')
    assert len(visitors) == 2
    visitor2 = visitors[1]
    assert visitor2['cookie'] == cookie
    assert visitor2['hits'] == 1
