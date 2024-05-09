from sqlalchemy import Column, Integer, MetaData, Table, create_engine, DateTime, Enum, func
from databases import Database
from models import PurchaseStatuses

#DATABASE_URI = 'postgresql://admin:adminadmin@127.0.0.1:5432/postgres'
DATABASE_URI = 'postgresql://secUREusER:StrongEnoughPassword)@51.250.26.59:5432/postgres'

engine = create_engine(DATABASE_URI)
metadata = MetaData()

purchase = Table(
    'purchase',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('amount', Integer),
    Column('date', DateTime, default=func.now()),
    Column('status', Enum(PurchaseStatuses))
)

database = Database(DATABASE_URI)

