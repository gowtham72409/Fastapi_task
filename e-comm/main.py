from fastapi import FastAPI
from router import orders,cart,auth,products
from utils import auth_handler
from database import Base,engine

app=FastAPI()

Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
