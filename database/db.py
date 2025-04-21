import sqlite3
import os
from models.user import UserInDB, User
from typing import List

# Cambia de base de datos si estás en modo test
DB_PATH = "test_users.db" if os.getenv("TESTING") == "1" else "database/users.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 username TEXT UNIQUE, 
                 email TEXT UNIQUE, 
                 full_name TEXT, 
                 hashed_password TEXT)''')
    conn.commit()
    conn.close()

def get_user_by_id(user_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email, full_name, hashed_password FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return UserInDB(
            id=user[0],
            username=user[1],
            email=user[2],
            full_name=user[3],
            hashed_password=user[4]
        )
    return None

def get_user(username: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email, full_name, hashed_password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return UserInDB(
            id=user[0],
            username=user[1],
            email=user[2],
            full_name=user[3],
            hashed_password=user[4]
        )
    return None

def create_user(username: str, email: str, full_name: str, hashed_password: str):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO users (username, email, full_name, hashed_password) VALUES (?, ?, ?, ?)",
              (username, email, full_name, hashed_password))
    conn.commit()
    conn.close()

def get_all_users() -> List[User]:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, email, full_name FROM users")
    users = c.fetchall()
    conn.close()
    return [User(id=user[0], username=user[1], email=user[2], full_name=user[3]) for user in users]

# Inicializa la base de datos al arrancar la app
init_db()
