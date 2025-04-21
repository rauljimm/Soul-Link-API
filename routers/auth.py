from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User, UserCreate, LoginRequest, Token
from database.db import get_user, get_user_by_id, create_user, get_all_users
from auth.dependencies import verify_password, get_password_hash, authenticate_user, get_current_user
from auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from typing import List

router = APIRouter()

@router.post("/register", response_model=User)
async def register(user: UserCreate):
    db_user = get_user(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    create_user(user.username, user.email, user.full_name, hashed_password)
    
    # Fetch the newly created user to get the ID
    new_user = get_user(user.username)
    return User(id=new_user.id, username=new_user.username, email=new_user.email, full_name=new_user.full_name)

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/users/{user_id}/hash")
async def get_user_hash(user_id: int, current_user: User = Depends(get_current_user)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Only allow admins or the user themselves to access the hash (example logic)
    if current_user.username != user.username:
        raise HTTPException(status_code=403, detail="Not authorized to access this user's hash")
    return {"hashed_password": user.hashed_password}

@router.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_user)):
    return get_all_users()