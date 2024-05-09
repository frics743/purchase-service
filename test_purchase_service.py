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


# db_manager.py Тесты

# Тест добавления purchase
@pytest.mark.asyncio
async def test_add_purchase():
    test_data = PurchaseIn(amount=100, date=date, status=status)
    with patch('app.api.db_manager.database.execute', new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = test_data
        response = await add_purchase(test_data)
        assert response == test_data


# Тест получения всех purchase
@pytest.mark.asyncio
async def test_get_all_purchase():
    with patch('app.api.db_manager.database', new_callable=AsyncMock) as mock_database:
        mock_database.fetch_all.return_value = mock_purchase_data
        response = await get_all_purchase()
        assert response == mock_purchase_data
        mock_database.fetch_all.return_value = []
        with pytest.raises(HTTPException) as exc_info:
            await get_all_purchase()
        assert exc_info.value.status_code == 404


# Тест получения purchase по id
@pytest.mark.asyncio
async def test_get_purchase():
    with patch('app.api.db_manager.database.fetch_one', new_callable=AsyncMock) as mock_db:
        mock_db.return_value = mock_purchase_data[1]
        response = await get_purchase(1)
        assert response == mock_purchase_data[1]
    # Тестирование исключения, если purchase не найден
    with patch('app.api.db_manager.database.fetch_one', new_callable=AsyncMock) as mock_db:
        mock_db.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await get_purchase(1)
        assert exc_info.value.status_code == 404


# Тест удаления purchase по id
@pytest.mark.asyncio
async def test_delete_purchase():
    with patch('app.api.db_manager.database', new_callable=AsyncMock) as mock_delete_purchase:
        mock_delete_purchase.fetch_all.return_value = mock_purchase_data
        mock_delete_purchase.execute.return_value = 1
        response = await delete_purchase(1)
        assert response == 1

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
    with patch('app.api.db_manager.database.execute', new_callable=AsyncMock) as mock_execute:
        status_test = status
        date_test = date
        test_payload = PurchaseUpdate(id=1, amount=200, date=date_test, status=status_test)
        mock_execute.return_value = 1
        response = await update_purchase(id=1, payload=test_payload)
        assert response == {'id': 1, 'amount': 200, 'date': date_test, 'status': status_test}
        # Тест обновления несуществующего purchase
        mock_execute.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await update_purchase(id=99, payload=test_payload)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == 'Purchase not found'


# purchases.py Тесты


# Тест добавления purchase
@pytest.mark.asyncio
async def test_create_purchase():
    test_data = PurchaseIn(amount=100, date=date, status=status)
    test_response_data = {'id': 1, **test_data.model_dump()}
    with patch('app.api.purchases.add_purchase', new_callable=AsyncMock) as mock_create_purchase:
        mock_create_purchase.return_value = 1
        response = await create_purchase(test_data)
        mock_create_purchase.assert_awaited_with(test_data)
        assert response == test_response_data
    with patch('app.api.purchases.get_all_purchase', new_callable=AsyncMock) as mock_create_purchase:
        mock_create_purchase.side_effect = Exception()
        with pytest.raises(HTTPException) as exc_info:
            await create_purchase(test_data)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == 'Internal server error'


# Тест получения всех purchase
@pytest.mark.asyncio
async def test_get_purchases():
    with patch('app.api.purchases.get_all_purchase', new_callable=AsyncMock) as mock_get_all:
        mock_get_all.return_value = mock_purchase_data
        response = await get_purchases()
        assert response == mock_purchase_data
    with patch('app.api.purchases.get_all_purchase', new_callable=AsyncMock) as mock_get_all:
        mock_get_all.side_effect = Exception()
        with pytest.raises(HTTPException) as exc_info:
            await get_purchases()
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == 'Internal server error'


# Тест получения всех purchase по id
@pytest.mark.asyncio
async def test_get_purchase_by_id():
    with patch('app.api.purchases.get_purchase', new_callable=AsyncMock) as mock_get_purchase:
        mock_get_purchase.return_value = mock_purchase_data
        response = await get_purchase_by_id(1)
        assert response == mock_purchase_data
    # Тестирование исключения, если покупка не найдена
    with patch('app.api.purchases.get_purchase', new_callable=AsyncMock) as mock_get_purchase:
        mock_get_purchase.side_effect = HTTPException(status_code=404, detail='Purchase not found')
        with pytest.raises(HTTPException) as exc_info:
            await get_purchase_by_id(1)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == 'Purchase not found'
    with patch('app.api.purchases.get_purchase', new_callable=AsyncMock) as mock_get_purchase:
        mock_get_purchase.side_effect = Exception()
        with pytest.raises(HTTPException) as exc_info:
            await get_purchase_by_id(1)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == 'Internal server error'


# Тест обновления всех purchase по id
@pytest.mark.asyncio
async def test_update_purchase_from_db():
    test_data = PurchaseUpdate(amount=100, date=date, status=status)
    status_test = status
    date_test = date
    with patch('app.api.db_manager.database.execute', new_callable=AsyncMock) as mock_update_purchase_from_db:
        mock_update_purchase_from_db.return_value = 1
        response = await update_purchase_from_db(id=1, payload=test_data)
        assert response == {'id': 1, 'amount': 100, 'date': date_test, 'status': status_test}
    with patch('app.api.db_manager.database.execute', new_callable=AsyncMock) as mock_update_purchase_from_db:
        mock_update_purchase_from_db.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await update_purchase_from_db(1, test_data)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == 'Purchase not found'
    with patch('app.api.db_manager.database.execute', new_callable=AsyncMock) as mock_purchase_from_db:
        mock_purchase_from_db.side_effect = Exception()
        with pytest.raises(HTTPException) as exc_info:
            await update_purchase_from_db(1, test_data)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == 'Internal server error'


# Тест удаления всех purchase по id
@pytest.mark.asyncio
async def test_delete_purchase_by_id():
    with patch('app.api.purchases.get_purchase', new_callable=AsyncMock) as mock_get_purchase, \
         patch('app.api.purchases.delete_purchase', new_callable=AsyncMock) as mock_delete_purchase:
        mock_get_purchase.return_value = mock_purchase_data
        mock_delete_purchase.return_value = {'message': f'Purchase with ID {1} has been successfully deleted'}
        response = await delete_purchase_by_id(1)
        assert response == {'message': f'Purchase with ID {1} has been successfully deleted'}
    with patch('app.api.purchases.get_purchase', new_callable=AsyncMock) as mock_get_purchase:
        mock_get_purchase.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await delete_purchase_by_id(2)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == 'Purchase not found'
    with patch('app.api.purchases.get_purchase', new_callable=AsyncMock) as mock_get_purchase, \
         patch('app.api.purchases.delete_purchase', new_callable=AsyncMock) as mock_delete_purchase:
        mock_get_purchase.return_value = mock_purchase_data
        mock_delete_purchase.side_effect = Exception()
        with pytest.raises(HTTPException) as exc_info:
            await delete_purchase_by_id(2)
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == 'Internal server error'

