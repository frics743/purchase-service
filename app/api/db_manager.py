from fastapi import HTTPException

from models import PurchaseIn, PurchaseOut
from db import purchase, database


async def add_purchase(payload: PurchaseIn):
    query = purchase.insert().values(**payload.model_dump())
    return await database.execute(query=query)


async def get_all_purchase():
    try:
        query = purchase.select()
        result = await database.fetch_all(query=query)
        if result:
            return result
        raise HTTPException(status_code=404, detail='Purchases not found')
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')


async def get_purchase(id):
    try:
        query = purchase.select().where(purchase.c.id == id)
        result = await database.fetch_one(query=query)
        if result is None:
            raise HTTPException(status_code=404, detail='Purchase not found')
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')


async def update_purchase(id: int, payload: PurchaseIn):
    query = (
        purchase.update()
        .where(purchase.c.id == id)
        .values(amount=payload.amount, status=payload.status)
        .returning(purchase.c.id)
    )
    try:
        result = await database.execute(query=query)
        if not result:
            raise HTTPException(status_code=404, detail='Purchase not found')
        return {'id': id, **payload.model_dump()}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')


async def delete_purchase(id: int):
    try:
        query = purchase.delete().where(purchase.c.id == id)
        result = await database.execute(query=query)
        if result == 0:
            raise HTTPException(status_code=404, detail='Purchase not found')
        return result
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error')
