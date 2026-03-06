from pydantic import BaseModel

class AntiqueCreate(BaseModel):
    name:str
    description:str
    price:float
    category:str

class AntiqueRespsone(AntiqueCreate):
    int:str

    class Congif():
        orm_mode=True