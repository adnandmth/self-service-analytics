from passlib.context import CryptContext

"""
PassLib is a great Python package to handle password hashes.

It supports many secure hashing algorithms and utilities to work with them.

The recommended algorithm is "Bcrypt".
"""
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

"""
verifying what user input against the registered hashed password.

When user login, our database stores the hashed password instead of raw value,
therefore verify is used to compare the two params if they are a match!
"""
def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
