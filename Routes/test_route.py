from fastapi import APIRouter, HTTPException

route = APIRouter()
tag='Test'

@route.get("/test")
def root():
    return {"message": "Hello World"}