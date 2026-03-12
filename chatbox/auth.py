from passlib.context import CryptContext

pwd_hashed=CryptContext(schemes=["argon2"],deprecated="auto")

def hashed(password:str):
    return pwd_hashed.hash(password)

def verify(plain_password:str,hashed_password:str):
    return pwd_hashed.verify(plain_password,hashed_password)

