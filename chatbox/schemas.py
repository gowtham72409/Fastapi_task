from pydantic import BaseModel,EmailStr,Field

class UserCreate(BaseModel): 
    name:str
    email:EmailStr
    password:str=Field(min_length=6, max_length=64)

class Userlogin(BaseModel):
    email:EmailStr
    password:str=Field(min_length=6, max_length=64)


    