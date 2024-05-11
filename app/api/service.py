import requests
from fastapi import HTTPException
from requests import RequestException

PAYMENT_SERVICE_HOST_URL = 'http://payment_service:8010/api/payments/get_all_payments'


async def get_all_payments():
    try:
        response = requests.get(PAYMENT_SERVICE_HOST_URL)
        response.raise_for_status()
        data = response.json()
        return data
    except RequestException as e:
        raise HTTPException(status_code=500, detail='Service unavailable')

