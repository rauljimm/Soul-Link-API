import pytest
from fastapi.testclient import TestClient
from main import app
import sqlite3
import os
from unittest.mock import patch
from models.user import UserInDB, User

os.environ["TESTING"] = "1"

client = TestClient(app)

# ---------- 🔧 Inicialización de DB de prueba ----------
@pytest.fixture(autouse=True)
def setup_test_db():
    reset_test_db()

def reset_test_db():
    if os.path.exists("test_users.db"):
        os.remove("test_users.db")
    conn = sqlite3.connect("test_users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, 
                  email TEXT UNIQUE, 
                  full_name TEXT, 
                  hashed_password TEXT)''')
    conn.commit()
    conn.close()

# ---------- 🔁 Funciones de base de datos de prueba ----------
def get_user_test(username: str):
    conn = sqlite3.connect("test_users.db")
    c = conn.cursor()
    c.execute("SELECT id, username, email, full_name, hashed_password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user:
        return UserInDB(*user)
    return None

def get_user_by_id_test(user_id: int):
    conn = sqlite3.connect("test_users.db")
    c = conn.cursor()
    c.execute("SELECT id, username, email, full_name, hashed_password FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return UserInDB(*user)
    return None

def create_user_test(username: str, email: str, full_name: str, hashed_password: str):
    conn = sqlite3.connect("test_users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, email, full_name, hashed_password) VALUES (?, ?, ?, ?)",
              (username, email, full_name, hashed_password))
    conn.commit()
    conn.close()

def get_all_users_test():
    conn = sqlite3.connect("test_users.db")
    c = conn.cursor()
    c.execute("SELECT id, username, email, full_name FROM users")
    users = c.fetchall()
    conn.close()
    return [User(id=row[0], username=row[1], email=row[2], full_name=row[3]) for row in users]

# ---------- ✅ TESTS ----------
@pytest.mark.asyncio
async def test_register():
    with patch("database.db.get_user", side_effect=get_user_test), \
         patch("database.db.create_user", side_effect=create_user_test):
        response = client.post("/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword",
            "full_name": "Test User"
        })
        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User"
        }

@pytest.mark.asyncio
async def test_login_success():
    with patch("database.db.get_user", side_effect=get_user_test), \
         patch("database.db.create_user", side_effect=create_user_test):
        client.post("/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword",
            "full_name": "Test User"
        })

    with patch("database.db.get_user", side_effect=get_user_test):
        response = client.post("/login", json={
            "username": "testuser",
            "password": "securepassword"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_fail():
    with patch("database.db.get_user", side_effect=get_user_test), \
         patch("database.db.create_user", side_effect=create_user_test):
        client.post("/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword",
            "full_name": "Test User"
        })

    with patch("database.db.get_user", side_effect=get_user_test):
        response = client.post("/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"

@pytest.mark.asyncio
async def test_get_current_user():
    with patch("database.db.get_user", side_effect=get_user_test), \
         patch("database.db.create_user", side_effect=create_user_test):
        client.post("/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword",
            "full_name": "Test User"
        })

    with patch("database.db.get_user", side_effect=get_user_test):
        login_response = client.post("/login", json={
            "username": "testuser",
            "password": "securepassword"
        })
        token = login_response.json()["access_token"]

    with patch("database.db.get_user", side_effect=get_user_test):
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User"
        }

@pytest.mark.asyncio
async def test_list_users():
    with patch("database.db.get_user", side_effect=get_user_test), \
         patch("database.db.create_user", side_effect=create_user_test), \
         patch("database.db.get_all_users", side_effect=get_all_users_test):

        client.post("/register", json={
            "username": "testuser1",
            "email": "test1@example.com",
            "password": "securepassword",
            "full_name": "Test User 1"
        })
        client.post("/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "securepassword",
            "full_name": "Test User 2"
        })

        login_response = client.post("/login", json={
            "username": "testuser1",
            "password": "securepassword"
        })
        token = login_response.json()["access_token"]

        response = client.get("/users", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

        users = response.json()
        assert any(u["username"] == "testuser1" for u in users)
        assert any(u["username"] == "testuser2" for u in users)
