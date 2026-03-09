from jose import jwt,JWTError
from fastapi import Depends,HTTPException,status
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime,timedelta
from dotenv import load_dotenv
import models
import os

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_TIME=os.getenv("ACCESS_TOKEN_TIME")


def create_token(data:dict):
    to_encode=data.copy()
    expire=datetime.utcnow()+timedelta(minutes=int(ACCESS_TOKEN_TIME))
    to_encode.update({"exp":expire})
    access_token=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return access_token



