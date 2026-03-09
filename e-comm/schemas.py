from pydantic import BaseModel,EmailStr

class UserCreate(BaseModel):
    username:str
    email:EmailStr
    password:str

class Login(BaseModel):
    email:EmailStr
    password:str

class ProductCreate(BaseModel):
    name:str
    description:str
    price:float
    category:str
    quantity:int

class ProductUpdate(BaseModel):
    name:str
    description:str
    price:float
    category:str
    quantity:int


class CartAdd(BaseModel):
    product_id:int
    quantity:int

class Token(BaseModel):
    access_token:str
    token_type:str

    class Config:
        from_attributese=True