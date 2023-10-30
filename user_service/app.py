import os
import sys
import json
import datetime
import collections
import contextlib
import logging.config
import sqlite3
import typing
import logging
import secrets
import hashlib
import base64

from fastapi import FastAPI, Depends, Response, HTTPException, status, Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings

#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__) 


ALGORITHM = "pbkdf2_sha256"

class Settings():
    database = "./var/primary/fuse/user.db"
    #logging_config: str #= "./etc/logging.ini"

class UserRegisterModel(BaseModel):
    id: int
    username: str
    password: str
    roles: list[int]

class UserLoginModel(BaseModel):
    username: str
    password: str    

settings = Settings()
app = FastAPI()    

def get_db():
    with contextlib.closing(sqlite3.connect(settings.database)) as db:
        db.row_factory = sqlite3.Row
        yield db


def get_logger():
    return logging.getLogger(__name__)

#logging.config.fileConfig(settings.logging_config, disable_existing_loggers=False)    

def hash_password(password, salt=None, iterations=260000):
    if salt is None:
        salt = secrets.token_hex(16)
    assert salt and isinstance(salt, str) and "$" not in salt
    assert isinstance(password, str)
    pw_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    b64_hash = base64.b64encode(pw_hash).decode("ascii").strip()
    return "{}${}${}${}".format(ALGORITHM, iterations, salt, b64_hash)


def verify_password(password, password_hash):
    if (password_hash or "").count("$") != 3:
        return False
    algorithm, iterations, salt, b64_hash = password_hash.split("$", 3)
    iterations = int(iterations)
    assert algorithm == ALGORITHM
    compare_hash = hash_password(password, salt, iterations)
    return secrets.compare_digest(password_hash, compare_hash)

def expiration_in(minutes):
    creation = datetime.datetime.now(tz=datetime.timezone.utc)
    expiration = creation + datetime.timedelta(minutes=minutes)
    return creation, expiration


def generate_claims(username, user_id, roles):
    _, exp = expiration_in(20)

    claims = {
        "aud": "krakend.local.gd",
        "iss": "auth.local.gd",
        "sub": username,
        "jti": str(user_id),
        "roles": roles,
        "exp": int(exp.timestamp()),
    }
    token = {
        "access_token": claims,
        "refresh_token": claims,
        "exp": int(exp.timestamp()),
    }
    return token
 
    
# Operation/Resource 13
@app.post("/register/", description="Register a new user")
def register_new_user(usermodel: UserRegisterModel, db: sqlite3.Connection = Depends(get_db)):
    try:
        # Generate a random salt for each user 
        hashed_password = hash_password(usermodel.password)
        cursor = db.cursor()
        cursor.execute("INSERT INTO user(id, username, hashed_password) VALUES (?, ?, ?)",
                       (usermodel.id, usermodel.username, hashed_password))
        data = []
        for i in range(len(usermodel.roles)):
            data.append((usermodel.id, usermodel.roles[i]))
        cursor.executemany("INSERT INTO user_role(user_id, role_id) VALUES (?, ?)", data)
        db.commit()
        return {"message": "User registration successful"}
    except Exception as e:
        #logger.exception("An error occurred during user registration")
        raise HTTPException(status_code=500, detail="User registration failed")

# Operation/Resource 14
@app.post("/login/", description="User Login")
def login(logindata: UserLoginModel, db: sqlite3.Connection = Depends(get_db)):
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id, hashed_password FROM user WHERE username=? LIMIT 1", [logindata.username])
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="wrong username & password combination") 

        if not verify_password(logindata.password, result["hashed_password"]):
            raise HTTPException(status_code=404, detail="Password mismatch")
        else:
            cursor.execute('''SELECT roles.role_name
                              FROM roles INNER JOIN user_role ON roles.id = user_role.role_id
                              WHERE user_role.user_id = ? ''', [result["id"]])
            rows = cursor.fetchall()       
            list_of_rolenames = [row[0] for row in rows]
            return generate_claims(logindata.username, result["id"], list_of_rolenames)
            

    except Exception as e:
        #logger.exception("An error occurred during password verification")    
        #raise HTTPException(status_code=e.status_code, detail=str(e.detail)) 
        raise HTTPException(status_code=500, detail="User login failed")
    
    

@app.get("/test/", description="User Login")
def check_user_password(logindata: UserLoginModel, db: sqlite3.Connection = Depends(get_db)):
    return {"message": "Password mismatch"}

@app.get('/users/', description = 'View all users')
def list_users(db:sqlite3.Connection = Depends(get_db)):
    users = db.execute("SELECT * FROM user")
    return {"users":users.fetchall()}