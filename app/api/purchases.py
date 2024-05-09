from fastapi import APIRouter, Depends, HTTPException
from typing_extensions import List, Annotated
import logging
from models import PurchaseOut, PurchaseIn, PurchaseUpdate
from .db_manager import add_purchase, get_all_purchase, get_purchase, delete_purchase, update_purchase
from .db import database

purchases = APIRouter()


@purchases.post('/create_purchase', response_model=PurchaseOut, status_code=201)
async def create_purchase(payload: Annotated[PurchaseIn, Depends()]):
    try:
        purchase_id = await add_purchase(payload)
        response = {
            'id': purchase_id,
            **payload.model_dump()
        }
        return response
    except HTTPException as http_exc:
        # Переадресация исключений от функции add_purchase
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')


@purchases.get('/get_purchases', response_model=List[PurchaseOut])
async def get_purchases():
    try:
        return await get_all_purchase()
    except HTTPException as http_exc:
        # Переадресация исключений от функции get_all_purchase()
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')


@purchases.get('/{id}/', response_model=PurchaseOut)
async def get_purchase_by_id(id: int):
    try:
        purchases_by_id = await get_purchase(id)
        return purchases_by_id
    except HTTPException as http_exc:
        # Переопределение исключений от функции get_purchase()
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')


@purchases.put('/update_purchases/{id}/', response_model=PurchaseOut)
async def update_purchase_from_db(id: int, payload: PurchaseUpdate = Depends()):
    try:
        return await update_purchase(id, payload)
    except HTTPException as http_exc:
        # Переопределение исключений от функции update_purchase()
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')


@purchases.delete('/{id}/', response_model=None)
async def delete_purchase_by_id(id: int):
    try:
        purchases_by_id = await get_purchase(id)
        if not purchases_by_id:
            raise HTTPException(status_code=404, detail='Purchase not found')
        await delete_purchase(id)
        return {'message': f'Purchase with ID {id} has been successfully deleted'}
    except HTTPException as http_exc:
        # Переопределение исключений от функции delete_purchase()
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')
