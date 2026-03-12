from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import models, schemas
from auth import hashed, verify
from database import get_db

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/register")
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = hashed(user.password)
    db_user = models.User(name=user.name, email=user.email, password=hashed_password)
    db.add(db_user)
    db.commit()
    return {"message": "User registered successfully"}

@router.post("/login")
def login(user: schemas.Userlogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Return the user ID directly so the frontend can use it for the WebSocket
    return {"user_id": db_user.id, "name": db_user.name}