from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from Routes.test_route import route as test_route
from Routes.clasificacion_route import route as clasificacion_route
from Config.settings import SECRET_KEY
import os

app = FastAPI(title="Futbol API")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\python\\venv\\source\\soy-radius-332400-33f444dab422.json"

def verify_api_key(api_key: str = Header(...)):
    if api_key != SECRET_KEY:
        raise HTTPException(status_code=409, detail="Invalid API key")

app.include_router(test_route, dependencies=[Depends(verify_api_key)])
app.include_router(clasificacion_route, dependencies=[Depends(verify_api_key)])