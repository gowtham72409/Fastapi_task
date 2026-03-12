import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
import mysql.connector


Database_url ="mysql+pymysql://root:242002@localhost:3306/chat_db"

engine=create_engine(Database_url)
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)

Base=declarative_base()

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()