from sqlalchemy import Column,String,Integer,Float,ForeignKey
from database import Base

class User(Base):
    __tablename__="users"

    id=Column(Integer,primary_key=True,index=True)
    username=Column(String(100))
    email=Column(String(100),unique=True)
    password=Column(String(500))

class Product(Base):
    __tablename__="products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(String(200))
    price = Column(Float)
    category = Column(String(100))
    quantity = Column(Integer)

class Cart(Base):
    __tablename__="cart"

    id = Column(Integer, primary_key=True, index=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    product_id=Column(Integer,ForeignKey("products.id"))
    quantity = Column(Integer)
    
class Order(Base):
    __tablename__="orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id=Column(Integer,ForeignKey("users.id"))
    total_price=Column(Float)

class OrderItem(Base):
    __tablename__="order_items"

    id = Column(Integer, primary_key=True)
    order_id=Column(Integer,ForeignKey("orders.id"))
    product_id=Column(Integer,ForeignKey("products.id"))
    quantity=Column(Integer)
    price=Column(Float)





