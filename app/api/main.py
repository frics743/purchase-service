from fastapi import FastAPI
from .purchases import purchases
from db import metadata, database, engine

metadata.create_all(engine)

app = FastAPI(title='Online store for board games: Purchase')


@app.on_event('startup')
async def startup_event():
    await database.connect()


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()

app.include_router(purchases, prefix='/api/purchases', tags=['Purchases'])

