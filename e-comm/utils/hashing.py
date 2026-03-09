from passlib.context import CryptContext

pwd_hash=CryptContext(schemes=["argon2"],deprecated="auto")

def hash_password(password):
    return pwd_hash.hash(password)

def verify_password(plain,hashed):
    return pwd_hash.verify(plain,hashed)