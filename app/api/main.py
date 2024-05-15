from fastapi import FastAPI, HTTPException, Form, Header
from keycloak.keycloak_openid import KeycloakOpenID
from prometheus_fastapi_instrumentator import Instrumentator
from .purchases import purchases
from db import metadata, database, engine

metadata.create_all(engine)

app = FastAPI(title='Online store for board games: Purchase', openapi_url='/api/purchases/openapi.json',
              docs_url='/docs')

Instrumentator().instrument(app).expose(app)

#pip install prometheus_fastapi_instrumentator
#sum(count_over_time({job="docker"} |~ "status=200" [1m])) loki
#rate(process_cpu_seconds_total[5m]) prom CPU usage
#prometheus_http_requests_total{instance="prometheus:9090", handler="/api/v1/query_range"} prom Requests to the purchase-service
#prometheus_http_response_size_bytes_sum{instance="prometheus:9090", job="prometheus", handler="/api/v1/query_range"} prom Network (bytes)
#{job="docker"} |= purchase-service |= status_code=200 loki Log Data
#sum(count_over_time({job="docker"} |~ "status=200" [10m])) loki Successful operations
#docker compose up --build

#purchaseuser
#admin

#KEYCLOAK_URL = 'http://localhost:8080/'
KEYCLOAK_URL = 'http://keycloak:8080/'
KEYCLOAK_CLIENT_ID = 'purchaseClient'
KEYCLOAK_REALM = 'master'
KEYCLOAK_CLIENT_SECRET = 'HDc7n5E4NYqVHbrOk8zq3n6C0hoo6g0x'

keycloak_openid = KeycloakOpenID(server_url=KEYCLOAK_URL,
                                 client_id=KEYCLOAK_CLIENT_ID,
                                 realm_name=KEYCLOAK_REALM,
                                 client_secret_key=KEYCLOAK_CLIENT_SECRET)


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        token = keycloak_openid.token(grant_type=['password'],
                                      username=username,
                                      password=password)
        return token
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail='Failed to get token')


def user_got_role(token):
    try:
        token_info = keycloak_openid.introspect(token)
        if 'purchaseRole' not in token_info['realm_access']['roles']:
            raise HTTPException(status_code=403, detail='Access denied')
        return token_info
    except Exception as e:
        raise HTTPException(status_code=401, detail='Invalid token or access denied')


@app.put("/connect")
async def startup(token: str = Header()):
    if user_got_role(token):
        await database.connect()
        return {'message': 'Database connected'}
    else:
        return 'Wrong JWT Token'


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()

app.include_router(purchases, prefix='/api/purchases', tags=['Purchases'])

