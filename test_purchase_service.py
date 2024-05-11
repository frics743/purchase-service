#Unit

import random
import pytest
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.api.models import PurchaseIn, PurchaseStatuses, PurchaseUpdate
from app.api.db_manager import get_all_purchase, get_purchase, add_purchase, delete_purchase, update_purchase
from app.api.purchases import (get_purchase_by_id, get_purchases, create_purchase, update_purchase_from_db,
                               delete_purchase_by_id)
from app.api.db import purchase


amount = random.randint(1, 100000)
date = datetime.now() - timedelta(days=random.randrange(3650), seconds=random.randrange(86400))
status = random.choice(list(PurchaseStatuses))

mock_purchase_data = [
    {'id': 1, 'amount': amount, 'date': date, 'status': status},
    {'id': 2, 'amount': amount, 'date': date, 'status': status},
    {'id': 3, 'amount': amount, 'date': date, 'status': status}
]


# models.py Тесты

# Проверка полей таблицы
@pytest.fixture()
def any_purchase() -> PurchaseIn:
    return PurchaseIn(amount=amount, date=date, status=status)


def test_purchase_creation(any_purchase: PurchaseIn):
    assert dict(any_purchase) == {'amount': amount, 'date': date, 'status': status}


def test_purchase_amount(any_purchase: PurchaseIn):
    with pytest.raises(Exception):
        PurchaseIn(date=date, status=status)
    with pytest.raises(Exception):
        PurchaseIn(amount='-', date=date, status=status)
    with pytest.raises(Exception):
        PurchaseIn(amount=1.1, date=date, status=status)


def test_purchase_date(any_purchase: PurchaseIn):
    with pytest.raises(Exception):
        PurchaseIn(amount=amount, date='-', status=status)


def test_purchase_status(any_purchase: PurchaseIn):
    with pytest.raises(Exception):
        PurchaseIn(amount=amount, date=date)
    with pytest.raises(Exception):
        PurchaseIn(amount=amount, date=date, status='-')
    with pytest.raises(Exception):
        PurchaseIn(amount=amount, date=date, status=1)
    with pytest.raises(Exception):
        PurchaseIn(amount=amount, date=date, status='READY')


# db_manager.py Тесты

# Тест добавления purchase
@pytest.mark.asyncio
async def test_add_purchase():
    test_data = PurchaseIn(amount=amount, date=date, status=status)
    expected_response = {'id': 1, 'amount': amount, 'date': date, 'status': status}
    with patch('app.api.db_manager.database.execute', new_callable=AsyncMock) as mock_database:
        mock_database.return_value = expected_response
        response = await add_purchase(test_data)
        assert response == expected_response


# Тест получения всех purchase
@pytest.mark.asyncio
async def test_get_all_purchase():
    expected_response = [
        {'id': 1, 'amount': amount, 'date': date, 'status': status},
        {'id': 2, 'amount': amount, 'date': date, 'status': status},
        {'id': 3, 'amount': amount, 'date': date, 'status': status}
    ]
    with patch('app.api.db_manager.database', new_callable=AsyncMock) as mock_database:
        mock_database.fetch_all.return_value = expected_response
        response = await get_all_purchase()
        assert response == expected_response
        mock_database.fetch_all.return_value = []
        with pytest.raises(HTTPException) as exc_info:
            await get_all_purchase()
        assert exc_info.value.status_code == 404


# Тест получения purchase по id
@pytest.mark.asyncio
async def test_get_purchase():
    test_data = 1
    expected_response = {'id': 1, 'amount': amount, 'date': date, 'status': status}
    with patch('app.api.db_manager.database.fetch_one', new_callable=AsyncMock) as mock_database:
        mock_database.return_value = expected_response
        response = await get_purchase(test_data)
        assert response == expected_response
    # Тестирование исключения, если purchase не найден
    with patch('app.api.db_manager.database.fetch_one', new_callable=AsyncMock) as mock_database:
        mock_database.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await get_purchase(test_data)
        assert exc_info.value.status_code == 404


# Тест удаления purchase по id
@pytest.mark.asyncio
async def test_delete_purchase():
    test_data = 1
    expected_response = [
        {'id': 1, 'amount': amount, 'date': date, 'status': status},
        {'id': 2, 'amount': amount, 'date': date, 'status': status},
        {'id': 3, 'amount': amount, 'date': date, 'status': status}
    ]
    with patch('app.api.db_manager.database', new_callable=AsyncMock) as mock_database:
        mock_database.fetch_all.return_value = expected_response
        mock_database.execute.return_value = test_data
        response = await delete_purchase(test_data)
        assert response == test_data

    async def mock_execute(query):
        assert 'WHERE purchase.id =' in str(query)
        return 0
    # Тест удаления несуществующего purchase
    with patch('app.api.db_manager.database.execute', new=mock_execute):
        with pytest.raises(HTTPException) as exc_info:
            await delete_purchase(4)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == 'Purchase not found'


# Тест обновления purchase по id
@pytest.mark.asyncio
async def test_update_purchase():
    with patch('app.api.db_manager.database.execute', new_callable=AsyncMock) as mock_database:
        test_payload = PurchaseUpdate(id=1, amount=200, date=date, status=status)
        mock_database.return_value = 1
        response = await update_purchase(id=1, payload=test_payload)
        assert response == {'id': 1, 'amount': 200, 'date': date, 'status': status}
        # Тест обновления несуществующего purchase
        mock_database.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await update_purchase(id=99, payload=test_payload)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == 'Purchase not found'
