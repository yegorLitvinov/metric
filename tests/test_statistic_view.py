from datetime import date
from unittest import mock
from uuid import uuid4

import pytest

from app.visitor.models import Visitor

pytestmark = pytest.mark.asyncio


async def test_statistic_unauthenticated(db, client):
    response = await client.get('/api/statistic/')
    assert response.status == 401


async def test_statistic_success(user, login, client):
    now = date(2018, 2, 23)
    yesterday = date(2018, 2, 22)
    v1 = Visitor(
        account_id=user.id,
        path='/one',
        date=yesterday,
        cookie=uuid4(),
        hits=2,
    )
    v2 = Visitor(
        account_id=user.id,
        path='/one',
        date=now,
        cookie=uuid4(),
    )
    for v in v1, v2:
        await v.save()
    await login(user)
    with mock.patch('app.statistic.views.datetime') as datetime_mock:
        datetime_mock.now.return_value = now
        response = await client.get('/api/statistic/', params={'filter_by': 'month'})
    assert response.status == 200
    data = await response.json()
    assert data == {
        'hits': 3,
        'visits': 2,
        'paths': [
            {'path': '/one', '_sum': 3}
        ]
    }
