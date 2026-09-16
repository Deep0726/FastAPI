from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from models import User
from passlib.context import CryptContext
from database import SessionLocal
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt, JWTError

router= APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = "a50ef10ca388b07c9e4f7b74898e342993f64f2d142c1c52f6a38b2a08eecda6"
ALGORITHM = "HS256"
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")

class CreateUserRequest(BaseModel):

    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

def get_db():
    db= SessionLocal()
    try:
        yield  db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(db: db_dependency ,create_user_request: CreateUserRequest):
    create_user_model = User(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        hashed_password= bcrypt_context.hash(create_user_request.password),
        role = create_user_request.role,
        is_active= True
    )

    db.add(create_user_model)
    db.commit()

def verify_user(username: str, password:str, db):
    fetch_user = db.query(User).filter(User.username == username).first()
    if not fetch_user:
        return  False
    if not bcrypt_context.verify(password, fetch_user.hashed_password):
        return False
    return fetch_user

def create_access_token(username: str, user_id:int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return  jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        username = payload.get("sub")
        user_id = payload.get("id")
        if username is None and user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Couldn't validate user")
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Access")
@router.post("/token")
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                           db: db_dependency):
    user = verify_user(form_data.username, form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Access")
    token = create_access_token(user.username, user.id, timedelta(minutes=20))

    return token