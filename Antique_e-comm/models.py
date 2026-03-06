from sqlalchemy import Column,Integer,String,Float
from database import Base

class Product(Base):
    __tablename__="antique"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String(50))
    description=Column(String(200))
    price=Column(Float)
    category=Column(String(200))