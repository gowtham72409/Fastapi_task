from fastapi import FastAPI,Request
from fastapi.templating import Jinja2Templates
from router import user,chat
from database import Base,engine
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI()
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

app.include_router(user.router)
app.include_router(chat.router)

@app.get("/")
def home(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})
