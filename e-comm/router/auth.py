from fastapi import APIRouter,Depends,HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from utils.hashing import hash_password,verify_password
from utils.auth_handler import create_token
from jose import jwt,JWTError
import models
import schemas
import os
from dotenv import load_dotenv 

load_dotenv()

router=APIRouter(prefix="/auth",tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_TIME=os.getenv("ACCESS_TOKEN_TIME")

@router.post("/register")
def create_user(user:schemas.UserCreate,db:Session=Depends(get_db)):
    hashed=hash_password(user.password)
    db_user=models.User(username=user.username,email=user.email,password=hashed)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message":"User register successfully"}


@router.post("/login", response_model=schemas.Token)
def login(user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Invalid email")
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=404, detail="Invalid password")

    access_token = create_token(data={"sub": db_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email=payload.get("sub")

        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
    
    except JWTError:
        raise HTTPException (status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="Invalid token")
    
    user=db.query(models.User).filter(models.User.email==email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Not found user")
    
    return user