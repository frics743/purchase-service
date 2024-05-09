import enum
from datetime import datetime
from pydantic import BaseModel
from typing_extensions import Optional


class PurchaseStatuses(enum.Enum):
    COLLECTED = 'collected'
    SENT = 'sent'
    READY = 'ready'
    ISSUED = 'issued'
    CANCELED = 'canceled'


class PurchaseIn(BaseModel):
    amount: int
    date: Optional[datetime] = None
    status: PurchaseStatuses


class PurchaseOut(PurchaseIn):
    id: int


class PurchaseUpdate(PurchaseIn):
    amount: int
    date: Optional[datetime] = None
    status: PurchaseStatuses
