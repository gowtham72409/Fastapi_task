from sqlalchemy import Column,Integer,String,Text,ForeignKey,DateTime
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__="user"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(100),unique=True)
    email=Column(String(100),unique=True)
    password=Column(String(500))

class Message(Base):
    __tablename__="message"

    id=Column(Integer,primary_key=True,index=True)
    sender_id=Column(Integer,ForeignKey("user.id"))
    receiver_id=Column(Integer,ForeignKey("user.id"))
    content=Column(Text)
    timestamp=Column(DateTime(timezone=True),server_default=func.now())

